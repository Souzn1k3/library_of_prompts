import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.client_tokens import candidate_scoped_tokens, scoped_client_token, scoped_or_random_token
from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, StoreItem, StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.model.store import (
    EconomyActionRead,
    PurchaseRead,
    PurchaseResult,
    StoreItemRead,
    StoreRewardRead,
)
from app.modules.economy.config.tuning import (
    DAILY_OFFER_ROTATION_SIZE,
    DEFAULT_BOOST_MISSIONS,
    DEFAULT_BOOST_PCT,
    DEFAULT_PREMIUM_DAYS,
    FIRST_PURCHASE_BONUS_LUMENS,
    LOCKED_CASHBACK_RATE,
    LOCKED_CASHBACK_REQUIRED_MISSIONS,
    LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS,
    NEAR_MISS_MAX_DELTA,
    PRICE_BAND_THRESHOLDS,
    SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
    SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
    SECOND_PURCHASE_CHALLENGE_REWARD,
    SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS,
)
from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_NAME,
    economy_experiment_metadata,
)
from app.modules.economy.model.wallet import WalletRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.wallet_service import WalletService


class StoreService:
    def __init__(
        self,
        store_repo: StoreRepository,
        wallet_repo: WalletRepository,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._store = store_repo
        self._wallet_repo = wallet_repo
        self._wallet = WalletService(wallet_repo, store_repo, analytics=analytics)
        self._analytics = analytics

    def _is_one_time_item(self, item: StoreItem) -> bool:
        return item.kind in {
            StoreItemKind.starter,
            StoreItemKind.subscription_discount,
            StoreItemKind.premium_prompt_unlock,
            StoreItemKind.prompt_bundle,
            StoreItemKind.boost,
        }

    def _scoped_client_token(self, user_id: uuid.UUID, raw_token: str, *, prefix: str = "store") -> str:
        return scoped_client_token(user_id, raw_token, prefix=prefix)

    def _effective_client_token(self, *, user_id: uuid.UUID, item: StoreItem, client_token: str | None) -> str:
        raw = (client_token or "").strip()
        if self._is_one_time_item(item):
            return self._scoped_client_token(user_id, f"one-time:{item.id}")
        if raw:
            return self._scoped_client_token(user_id, raw)
        return scoped_or_random_token(user_id, None, prefix="store")

    async def _find_purchase_by_client_token(self, *, user_id: uuid.UUID, client_token: str) -> Any | None:
        candidates = candidate_scoped_tokens(user_id, client_token, prefix="store")
        seen: set[str] = set()
        for token in candidates:
            if token in seen:
                continue
            seen.add(token)
            existing = await self._store.get_purchase_by_client_token(user_id=user_id, client_token=token)
            if existing is not None:
                return existing
        return None

    def _price_band(self, price: int) -> str:
        for threshold, label in PRICE_BAND_THRESHOLDS:
            if price <= threshold:
                return label
        return "premium"

    def _item_tags(self, row: StoreItem) -> list[str]:
        tags: list[str] = []
        if row.kind == StoreItemKind.starter:
            tags.append("starter")
        if row.kind == StoreItemKind.boost:
            tags.append("boost")
        if row.meta and isinstance(row.meta.get("tags"), list):
            tags.extend(str(tag) for tag in row.meta.get("tags", []) if tag)
        if row.kind == StoreItemKind.prompt_bundle and "best_value" not in tags:
            tags.append("best_value")
        out: list[str] = []
        for tag in tags:
            if tag not in out:
                out.append(tag)
        return out

    def _offer_window(self, now: datetime) -> datetime:
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return start + timedelta(days=1)

    def _daily_offer_rotation(self, items: list[StoreItem], *, now: datetime) -> set[str]:
        active = [item for item in items if item.is_active and (item.availability is None or item.availability > 0)]
        if not active:
            return set()
        seed = now.date().isoformat()
        scored = sorted(active, key=lambda item: sha256(f"{seed}:{item.slug}".encode("utf-8")).hexdigest())
        return {item.slug for item in scored[:DAILY_OFFER_ROTATION_SIZE]}

    async def _payer_status(self, user_id: uuid.UUID) -> str:
        return "payer" if await self._store.has_completed_purchase(user_id) else "non_payer"

    async def _track_store_experiment_view(
        self,
        *,
        user: User,
        payer_status: str,
        now: datetime,
        offer_slugs: set[str],
    ) -> None:
        if self._analytics is None:
            return
        experiment_meta = economy_experiment_metadata(user_id=user.id, payer_status=payer_status)
        variant = experiment_meta["experiment_variant"]
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.economy_experiment_assigned,
            user_id=user.id,
            metadata=experiment_meta,
            context_page="/api/v1/store",
            context_feature="ab_assignment",
            event_id=f"{ECONOMY_EXPERIMENT_NAME}:{user.id}:{payer_status}",
        )
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.store_offer_viewed,
            user_id=user.id,
            metadata={
                **experiment_meta,
                "offer_count": len(offer_slugs),
                "offer_slugs": sorted(offer_slugs),
                "offer_day": now.date().isoformat(),
            },
            context_page="/api/v1/store",
            context_feature="offer_impression",
            event_id=f"store_offer_viewed:{user.id}:{variant}:{now.date().isoformat()}",
        )

    async def _serialize_item(
        self,
        row: StoreItem,
        *,
        owned: bool = False,
        balance: int = 0,
        segment: str = "balanced",
        daily_offer_slugs: set[str] | None = None,
        offer_ends_at: datetime | None = None,
        active_boost_left_by_slug: dict[str, int] | None = None,
    ) -> StoreItemRead:
        sold_out = row.availability is not None and row.availability <= 0
        affordable = not sold_out and not owned and balance >= row.price
        remaining_lumens = max(row.price - balance, 0)
        progress_ratio = 1 if row.price <= 0 else round(min(balance, row.price) / row.price, 4)

        item_meta = row.meta or {}
        target_segment = str(item_meta.get("target_segment", "")).strip().lower()
        dynamic_offer = bool(target_segment and target_segment == segment)
        is_limited_offer = bool(daily_offer_slugs and row.slug in daily_offer_slugs)

        try:
            upgrade_tier = max(1, int(item_meta.get("upgrade_tier", 1)))
        except (TypeError, ValueError):
            upgrade_tier = 1
        try:
            max_tier = max(upgrade_tier, int(item_meta.get("max_tier", upgrade_tier)))
        except (TypeError, ValueError):
            max_tier = upgrade_tier

        boost_missions_left = None
        if active_boost_left_by_slug and row.slug in active_boost_left_by_slug:
            boost_missions_left = max(0, int(active_boost_left_by_slug[row.slug]))

        return StoreItemRead(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            price=row.price,
            kind=row.kind,
            availability=row.availability,
            metadata=row.meta,
            is_active=row.is_active,
            owned=owned,
            is_affordable=affordable,
            remaining_lumens=remaining_lumens,
            progress_ratio=progress_ratio,
            price_band=self._price_band(row.price),
            tags=self._item_tags(row),
            starter_type=item_meta.get("starter_type") if isinstance(item_meta.get("starter_type"), str) else None,
            is_limited_offer=is_limited_offer,
            offer_ends_at=offer_ends_at if is_limited_offer else None,
            offer_reason="daily_rotation" if is_limited_offer else ("personalized" if dynamic_offer else None),
            dynamic_offer=dynamic_offer,
            upgrade_tier=upgrade_tier,
            max_tier=max_tier,
            next_upgrade_cost=int(item_meta["next_upgrade_cost"]) if isinstance(item_meta.get("next_upgrade_cost"), int) else None,
            boost_pct=int(item_meta["boost_pct"]) if isinstance(item_meta.get("boost_pct"), int) else None,
            boost_missions_left=boost_missions_left,
            near_miss_delta=remaining_lumens,
        )

    async def _serialize_purchase(self, purchase, *, fallback_item: StoreItem | None = None, balance: int = 0) -> PurchaseRead:
        item = purchase.item or fallback_item
        if item is None:
            raise AppError(
                code="store_item_missing",
                message="Purchase item could not be loaded.",
                status_code=500,
                message_key="errors.store_item_missing",
            )
        return PurchaseRead(
            id=purchase.id,
            status=purchase.status,
            price_paid=purchase.price_paid,
            metadata=purchase.meta,
            client_token=purchase.client_token,
            item=await self._serialize_item(item, owned=True, balance=balance),
            created_at=purchase.created_at,
        )

    async def list_items(self, user: User, *, balance: int | None = None) -> list[StoreItemRead]:
        items = await self._store.list_active_items()
        if not items:
            premium_prompts = await self._store.list_featured_premium_prompts(limit=3)
            items = self._build_default_items(premium_prompts, stable_ids=True)

        if balance is None:
            balance, _, _ = await self._wallet_repo.summary(user.id)

        owned_item_ids = await self._store.list_owned_one_time_item_ids(user.id)
        segment = await self._wallet_repo.classify_user_segment(user_id=user.id)
        now = datetime.now(timezone.utc)
        payer_status = await self._payer_status(user.id)
        daily_offer_slugs = self._daily_offer_rotation(items, now=now)
        offer_ends_at = self._offer_window(now)

        active_boost_rows = await self._wallet_repo.list_active_boosts(user_id=user.id, now=now)
        active_boost_left_by_slug: dict[str, int] = {}
        for row in active_boost_rows:
            if not isinstance(row.meta, dict) or not isinstance(row.meta.get("item_slug"), str):
                continue
            slug = str(row.meta["item_slug"])
            active_boost_left_by_slug[slug] = max(
                active_boost_left_by_slug.get(slug, 0),
                max(0, int(row.missions_total) - int(row.missions_used)),
            )

        serialized = [
            await self._serialize_item(
                item,
                owned=item.id in owned_item_ids,
                balance=balance,
                segment=segment,
                daily_offer_slugs=daily_offer_slugs,
                offer_ends_at=offer_ends_at,
                active_boost_left_by_slug=active_boost_left_by_slug,
            )
            for item in items
        ]
        await self._track_store_experiment_view(
            user=user,
            payer_status=payer_status,
            now=now,
            offer_slugs=daily_offer_slugs,
        )
        return sorted(serialized, key=lambda item: (not item.is_limited_offer, item.price, item.remaining_lumens, item.title.lower()))

    def _pick_best_item(self, items: list[StoreItemRead]) -> StoreItemRead | None:
        purchasable = [
            item
            for item in items
            if item.is_active and not item.owned and (item.availability is None or item.availability > 0)
        ]
        if not purchasable:
            return None
        affordable = [item for item in purchasable if item.is_affordable]
        if affordable:
            return sorted(affordable, key=lambda item: ("starter" not in item.tags, item.price, item.title.lower()))[0]
        return sorted(purchasable, key=lambda item: (item.remaining_lumens, item.price, item.title.lower()))[0]

    async def build_action_feedback(
        self,
        user: User,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead:
        wallet = await self._wallet.get_wallet(user, limit=20)
        items = await self.list_items(user, balance=wallet.balance)
        available_items = [item for item in items if item.is_affordable]
        newly_affordable_items = [item for item in available_items if previous_balance is not None and previous_balance < item.price] if previous_balance is not None else []
        next_target = next((item for item in items if not item.owned and not item.is_affordable and item.remaining_lumens > 0), None)
        near_miss_message = (
            f"You need {next_target.remaining_lumens} LMN more for {next_target.title}."
            if next_target is not None and next_target.remaining_lumens <= NEAR_MISS_MAX_DELTA
            else None
        )
        return EconomyActionRead(
            wallet=wallet,
            balance=wallet.balance,
            available_items=available_items,
            newly_affordable_items=newly_affordable_items,
            best_item=self._pick_best_item(items),
            balance_delta=(wallet.balance - previous_balance) if previous_balance is not None else 0,
            completed_mission_slugs=completed_mission_slugs or [],
            near_miss_message=near_miss_message,
        )
    def _first_purchase_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="bonus_lumens",
            title="First purchase bonus",
            description="You spent Lumens once, so we topped up your wallet for the next unlock.",
            amount=amount,
            metadata={"reward_type": "first_purchase"},
        )

    def _locked_cashback_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="locked_cashback",
            title="Locked cashback added",
            description=(
                f"Complete {LOCKED_CASHBACK_REQUIRED_MISSIONS} missions in "
                f"{LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS} hours to unlock this cashback."
            ),
            amount=amount,
            metadata={
                "reward_type": "locked_cashback",
                "unlock_rule": f"{LOCKED_CASHBACK_REQUIRED_MISSIONS}_missions_{LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS}h",
            },
        )

    def _second_purchase_challenge_reward(self, amount: int) -> StoreRewardRead:
        return StoreRewardRead(
            kind="second_purchase_challenge",
            title="Second purchase challenge completed",
            description="Bonus Lumens and a short mission booster are now active.",
            amount=amount,
            metadata={
                "reward_type": "second_purchase",
                "boost_pct": SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                "boost_missions": SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
            },
        )

    def _reward_from_purchase_meta(self, meta: dict[str, Any] | None) -> StoreRewardRead | None:
        if not meta:
            return None
        amount = meta.get("first_purchase_bonus_amount")
        if isinstance(amount, int) and amount > 0:
            return self._first_purchase_reward(amount)
        return None

    async def _validate_upgrade_path(self, *, user: User, item: StoreItem) -> None:
        meta = item.meta or {}
        track = str(meta.get("upgrade_track") or "").strip().lower()
        tier_raw = meta.get("upgrade_tier")
        try:
            tier = int(tier_raw or 1)
        except (TypeError, ValueError):
            tier = 1
        if tier <= 1 or not track:
            return

        purchases = await self._store.list_all_completed_purchases(user.id)
        required_tier = tier - 1
        for purchase in purchases:
            payload = purchase.meta or {}
            payload_track = str(payload.get("upgrade_track") or "").strip().lower()
            if payload_track != track:
                continue
            try:
                payload_tier = int(payload.get("upgrade_tier") or 1)
            except (TypeError, ValueError):
                payload_tier = 1
            if payload_tier >= required_tier:
                return

        raise AppError(
            code="store_upgrade_locked",
            message="Upgrade tier is locked until previous tier is owned.",
            status_code=409,
            details={"upgrade_track": track, "required_tier": required_tier},
            message_key="errors.store_upgrade_locked",
        )

    def _apply_item_reward_metadata(self, *, item: StoreItem, purchase_metadata: dict[str, Any]) -> None:
        meta = item.meta or {}
        purchase_metadata["item_kind"] = item.kind.value
        purchase_metadata["upgrade_track"] = meta.get("upgrade_track")
        purchase_metadata["upgrade_tier"] = meta.get("upgrade_tier")

        if item.kind == StoreItemKind.starter:
            starter_type = str(meta.get("starter_type", "starter"))
            purchase_metadata["starter_type"] = starter_type
            purchase_metadata["reward_title"] = meta.get("reward_title") or item.title
            purchase_metadata["reward_body"] = meta.get("reward_body")
            if starter_type == "discount":
                percent = int(meta.get("discount_percent", 10))
                code = f"{meta.get('code_prefix', 'START')}-{secrets.token_hex(3).upper()}"
                purchase_metadata["discount_percent"] = percent
                purchase_metadata["discount_code"] = code
            return

        if item.kind == StoreItemKind.premium_pass:
            purchase_metadata["premium_days"] = int(meta.get("premium_days", DEFAULT_PREMIUM_DAYS))
            return

        if item.kind == StoreItemKind.subscription_discount:
            percent = int(meta.get("discount_percent", 20))
            code = f"{meta.get('code_prefix', 'LMN')}-{secrets.token_hex(3).upper()}"
            purchase_metadata["discount_percent"] = percent
            purchase_metadata["discount_code"] = code
            return

        if item.kind == StoreItemKind.premium_prompt_unlock:
            purchase_metadata["prompt_id"] = meta.get("prompt_id")
            purchase_metadata["prompt_slug"] = meta.get("prompt_slug")
            purchase_metadata["prompt_title"] = meta.get("prompt_title")
            return

        if item.kind == StoreItemKind.prompt_bundle:
            purchase_metadata["prompt_ids"] = list(meta.get("prompt_ids", []))
            purchase_metadata["prompt_slugs"] = list(meta.get("prompt_slugs", []))
            purchase_metadata["prompt_titles"] = list(meta.get("prompt_titles", []))
            purchase_metadata["bundle_size"] = len(purchase_metadata["prompt_ids"])
            return

        if item.kind == StoreItemKind.boost:
            purchase_metadata["boost_pct"] = int(meta.get("boost_pct", DEFAULT_BOOST_PCT))
            purchase_metadata["boost_missions"] = int(meta.get("boost_missions", DEFAULT_BOOST_MISSIONS))

    async def purchase(self, *, user: User, item_slug: str, client_token: str | None = None) -> PurchaseResult:
        if client_token:
            existing = await self._find_purchase_by_client_token(user_id=user.id, client_token=client_token)
            if existing is not None:
                feedback = await self.build_action_feedback(user)
                if feedback.wallet is None:
                    raise AppError(
                        code="wallet_missing",
                        message="Wallet could not be loaded.",
                        status_code=500,
                        message_key="errors.wallet_missing",
                    )
                wallet = feedback.wallet
                return PurchaseResult(
                    purchase=await self._serialize_purchase(existing, balance=wallet.balance),
                    wallet=wallet,
                    available_items=feedback.available_items,
                    newly_affordable_items=feedback.newly_affordable_items,
                    best_item=feedback.best_item,
                    first_purchase_reward=self._reward_from_purchase_meta(existing.meta),
                    locked_cashback_reward=None,
                    second_purchase_challenge_reward=None,
                )

        item = await self._store.get_item_by_slug(item_slug)
        if item is None:
            await self.sync_default_items()
            item = await self._store.get_item_by_slug(item_slug)
        if item is None or not item.is_active:
            raise AppError(
                code="store_item_not_found",
                message="Item is not available right now.",
                status_code=404,
                message_key="errors.store_item_not_found",
            )
        if item.availability is not None and item.availability <= 0:
            raise AppError(
                code="store_item_unavailable",
                message="This item is sold out.",
                status_code=409,
                message_key="errors.store_item_unavailable",
            )

        effective_client_token = self._effective_client_token(user_id=user.id, item=item, client_token=client_token)

        await self._validate_upgrade_path(user=user, item=item)

        if self._is_one_time_item(item):
            owned = await self._store.get_completed_purchase_for_item(user_id=user.id, item_id=item.id)
            if owned is not None:
                raise AppError(
                    code="store_item_owned",
                    message="You already own this unlock.",
                    status_code=409,
                    message_key="errors.store_item_owned",
                )
        if item.availability is not None:
            reserved = await self._store.decrement_availability_if_available(item.id)
            if not reserved:
                raise AppError(
                    code="store_item_unavailable",
                    message="This item is sold out.",
                    status_code=409,
                    message_key="errors.store_item_unavailable",
                )
            item.availability = max(item.availability - 1, 0)

        await self._wallet_repo.ensure_balance_row(user.id)
        previous_balance, _, _ = await self._wallet_repo.summary(user.id)
        had_purchase_before = await self._store.has_completed_purchase(user.id)
        payer_status = "payer" if had_purchase_before else "non_payer"
        experiment_meta = economy_experiment_metadata(user_id=user.id, payer_status=payer_status)

        now = datetime.now(timezone.utc)
        segment = await self._wallet_repo.classify_user_segment(user_id=user.id, now=now)
        daily_offer_slugs = self._daily_offer_rotation(await self._store.list_active_items(), now=now)
        is_limited_offer = item.slug in daily_offer_slugs
        target_segment = str((item.meta or {}).get("target_segment", "")).strip().lower()
        is_dynamic_offer = bool(target_segment and target_segment == segment)
        tier = int((item.meta or {}).get("upgrade_tier", 1)) if isinstance((item.meta or {}).get("upgrade_tier", 1), int) else 1
        purchase_reason = CurrencyTransactionType.store_purchase
        if item.kind == StoreItemKind.boost:
            purchase_reason = CurrencyTransactionType.boost_purchase
        if tier > 1:
            purchase_reason = CurrencyTransactionType.upgrade_purchase

        txn = await self._wallet_repo.adjust_balance(
            user_id=user.id,
            amount=-item.price,
            reason=purchase_reason,
            context=f"store:{item.slug}:{client_token or secrets.token_hex(4)}",
            source_id=item.id,
            metadata={
                "title": item.title,
                "item_kind": item.kind.value,
                "upgrade_tier": tier,
                "is_limited_offer": is_limited_offer,
                "is_dynamic_offer": is_dynamic_offer,
                **experiment_meta,
            },
            now=now,
        )

        spend_streak_days, spend_streak_mult = await self._wallet_repo.apply_purchase_streak(user.id, now=now)

        purchase_metadata: dict[str, Any] = {
            "transaction_id": str(txn.id),
            "spend_streak_days": spend_streak_days,
            "spend_streak_mult": spend_streak_mult,
        }
        self._apply_item_reward_metadata(item=item, purchase_metadata=purchase_metadata)

        if item.kind == StoreItemKind.premium_pass:
            days = int((item.meta or {}).get("premium_days", DEFAULT_PREMIUM_DAYS))
            premium_until = await self._wallet.grant_premium_days(user, days)
            purchase_metadata["premium_until"] = premium_until.isoformat()

        first_purchase_reward: StoreRewardRead | None = None
        if not had_purchase_before:
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=FIRST_PURCHASE_BONUS_LUMENS,
                reason=CurrencyTransactionType.first_purchase_bonus,
                context=f"store:first_purchase:{item.slug}:{client_token or secrets.token_hex(4)}",
                source_id=item.id,
                metadata={"item_slug": item.slug, "item_title": item.title},
                now=now,
            )
            purchase_metadata["first_purchase_bonus_amount"] = FIRST_PURCHASE_BONUS_LUMENS
            first_purchase_reward = self._first_purchase_reward(FIRST_PURCHASE_BONUS_LUMENS)
        try:
            purchase = await self._store.create_purchase(
                user_id=user.id,
                item=item,
                price_paid=item.price,
                client_token=effective_client_token,
                meta=purchase_metadata,
            )
        except IntegrityError as exc:
            await self._store.rollback()
            existing = await self._store.get_purchase_by_client_token(
                user_id=user.id,
                client_token=effective_client_token,
            )
            if existing is not None:
                if client_token:
                    feedback = await self.build_action_feedback(user)
                    if feedback.wallet is None:
                        raise AppError(
                            code="wallet_missing",
                            message="Wallet could not be loaded.",
                            status_code=500,
                            message_key="errors.wallet_missing",
                        )
                    wallet = feedback.wallet
                    return PurchaseResult(
                        purchase=await self._serialize_purchase(
                            existing,
                            balance=wallet.balance,
                        ),
                        wallet=wallet,
                        available_items=feedback.available_items,
                        newly_affordable_items=feedback.newly_affordable_items,
                        best_item=feedback.best_item,
                        first_purchase_reward=self._reward_from_purchase_meta(existing.meta),
                        locked_cashback_reward=None,
                        second_purchase_challenge_reward=None,
                    )
                raise AppError(
                    code="store_item_owned",
                    message="You already own this unlock.",
                    status_code=409,
                    message_key="errors.store_item_owned",
                ) from exc
            raise

        locked_cashback_reward: StoreRewardRead | None = None
        cashback_amount = int(item.price * LOCKED_CASHBACK_RATE)
        if cashback_amount > 0:
            unlock_by = now + timedelta(hours=LOCKED_CASHBACK_UNLOCK_WINDOW_HOURS)
            locked_reward = await self._wallet_repo.create_locked_cashback(
                user_id=user.id,
                amount=cashback_amount,
                source_purchase_id=purchase.id,
                unlock_by=unlock_by,
                metadata={"item_slug": item.slug, "item_title": item.title},
            )
            if locked_reward is not None:
                await self._wallet_repo.adjust_balance(
                    user_id=user.id,
                    amount=0,
                    reason=CurrencyTransactionType.cashback_locked,
                    context=f"cashback_locked:{locked_reward.id}",
                    source_id=locked_reward.id,
                    metadata={"locked_reward_id": str(locked_reward.id), "amount": cashback_amount, "unlock_by": unlock_by.isoformat()},
                    now=now,
                )
                locked_cashback_reward = self._locked_cashback_reward(cashback_amount)

        if item.kind == StoreItemKind.boost:
            await self._wallet_repo.grant_active_boost(
                user_id=user.id,
                source_purchase_id=purchase.id,
                boost_percent=int((item.meta or {}).get("boost_pct", DEFAULT_BOOST_PCT)),
                missions_total=int((item.meta or {}).get("boost_missions", DEFAULT_BOOST_MISSIONS)),
                metadata={"item_slug": item.slug, "item_title": item.title},
            )

        second_purchase_challenge_reward: StoreRewardRead | None = None
        challenge_state = await self._wallet_repo.track_second_purchase_challenge(user_id=user.id, now=now)
        if challenge_state == "started":
            purchase_metadata["second_purchase_challenge_expires_at"] = (
                now + timedelta(hours=SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS)
            ).isoformat()
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.second_purchase_challenge_started,
                    user_id=user.id,
                    metadata={
                        **experiment_meta,
                        "purchase_id": str(purchase.id),
                        "item_slug": item.slug,
                        "expires_at": purchase_metadata["second_purchase_challenge_expires_at"],
                    },
                    context_page="/api/v1/store",
                    context_feature="second_purchase_challenge",
                    event_id=f"second_purchase_challenge_started:{user.id}:{purchase.id}",
                )
        if challenge_state == "completed":
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=SECOND_PURCHASE_CHALLENGE_REWARD,
                reason=CurrencyTransactionType.rank_bonus,
                context=f"second_purchase_challenge:{purchase.id}",
                source_id=purchase.id,
                metadata={"challenge": "second_purchase", "item_slug": item.slug},
                now=now,
            )
            await self._wallet_repo.grant_active_boost(
                user_id=user.id,
                source_purchase_id=purchase.id,
                boost_percent=SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                missions_total=SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
                metadata={"item_slug": "challenge_boost", "source": "second_purchase_challenge"},
            )
            second_purchase_challenge_reward = self._second_purchase_challenge_reward(SECOND_PURCHASE_CHALLENGE_REWARD)
            if self._analytics is not None:
                await self._analytics.record_server_event(
                    event_name=AnalyticsEventName.second_purchase_challenge_completed,
                    user_id=user.id,
                    metadata={
                        **experiment_meta,
                        "purchase_id": str(purchase.id),
                        "item_slug": item.slug,
                        "reward_lmn": SECOND_PURCHASE_CHALLENGE_REWARD,
                        "reward_boost_pct": SECOND_PURCHASE_CHALLENGE_BOOST_PCT,
                        "reward_boost_missions": SECOND_PURCHASE_CHALLENGE_BOOST_MISSIONS,
                    },
                    context_page="/api/v1/store",
                    context_feature="second_purchase_challenge",
                    event_id=f"second_purchase_challenge_completed:{user.id}:{purchase.id}",
                )

        purchase.meta = purchase_metadata

        feedback = await self.build_action_feedback(user, previous_balance=previous_balance)
        if feedback.wallet is None:
            raise AppError(
                code="wallet_missing",
                message="Wallet could not be loaded.",
                status_code=500,
                message_key="errors.wallet_missing",
            )

        if self._analytics is not None:
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.store_purchase_completed,
                user_id=user.id,
                metadata={
                    **experiment_meta,
                    "purchase_id": str(purchase.id),
                    "item_slug": item.slug,
                    "item_kind": item.kind.value,
                    "price_lmn": int(item.price),
                    "balance_before": int(previous_balance),
                    "balance_after": int(feedback.wallet.balance),
                    "is_limited_offer": is_limited_offer,
                    "is_dynamic_offer": is_dynamic_offer,
                    "segment": segment,
                    "locked_cashback_amount": cashback_amount,
                    "second_purchase_challenge_state": challenge_state,
                },
                context_page="/api/v1/store",
                context_feature="purchase",
                event_id=f"store_purchase_completed:{user.id}:{purchase.id}",
            )

        return PurchaseResult(
            purchase=await self._serialize_purchase(purchase, fallback_item=item, balance=feedback.wallet.balance),
            wallet=feedback.wallet,
            available_items=feedback.available_items,
            newly_affordable_items=feedback.newly_affordable_items,
            best_item=feedback.best_item,
            first_purchase_reward=first_purchase_reward,
            locked_cashback_reward=locked_cashback_reward,
            second_purchase_challenge_reward=second_purchase_challenge_reward,
        )

    async def wallet(self, user: User) -> WalletRead:
        return await self._wallet.get_wallet(user, limit=25)

    def _build_default_items(self, premium_prompts: list[Any], *, stable_ids: bool = False) -> list[StoreItem]:
        def make_item(*, slug: str, **kwargs: Any) -> StoreItem:
            item_kwargs = {"slug": slug, "is_active": True, **kwargs}
            if stable_ids:
                item_kwargs["id"] = uuid.uuid5(uuid.NAMESPACE_URL, f"store:{slug}")
            return StoreItem(**item_kwargs)

        defaults: list[StoreItem] = [
            make_item(
                slug="starter-mini-prompt",
                title="Starter Mini Prompt",
                description="Unlock a compact prompt you can paste instantly for clearer AI answers.",
                price=5,
                kind=StoreItemKind.starter,
                meta={"starter_type": "mini_prompt", "reward_title": "Reply starter", "reward_body": "Act as an expert editor. Rewrite my draft in 3 clearer bullet points with one concrete next step.", "tags": ["starter", "popular"], "synergy_categories": ["prompt"], "upgrade_track": "starter-track", "upgrade_tier": 1, "max_tier": 3, "next_upgrade_cost": 6},
                sort_order=1,
            ),
            make_item(
                slug="starter-structure-fragment",
                title="Starter Structure Fragment",
                description="Get a reusable response fragment that turns vague outputs into actionable structure.",
                price=6,
                kind=StoreItemKind.starter,
                meta={"starter_type": "fragment", "reward_title": "Output fragment", "reward_body": "Return the answer as: 1) core idea 2) risks 3) next action 4) one better version.", "tags": ["starter"], "synergy_categories": ["prompt", "progress"], "upgrade_track": "starter-track", "upgrade_tier": 2, "max_tier": 3, "next_upgrade_cost": 8},
                sort_order=2,
            ),
            make_item(
                slug="starter-spark-discount",
                title="Starter Spark Discount",
                description="Turn your first Lumens into a small checkout discount code you can use right away.",
                price=8,
                kind=StoreItemKind.starter,
                meta={"starter_type": "discount", "discount_percent": 15, "code_prefix": "START", "reward_title": "15% checkout code", "reward_body": "A small discount for your next checkout, unlocked with starter-tier Lumens.", "tags": ["starter", "best_value"], "synergy_categories": ["spend"], "upgrade_track": "starter-track", "upgrade_tier": 3, "max_tier": 3},
                sort_order=3,
            ),
            make_item(slug="booster-s", title="Booster S", description="Increase LMN rewards by 20% for your next 3 mission completions.", price=5, kind=StoreItemKind.boost, meta={"boost_pct": 20, "boost_missions": 3, "tags": ["entry", "boost"], "synergy_categories": ["progress", "spend"], "upgrade_track": "booster-core", "upgrade_tier": 1, "max_tier": 3, "next_upgrade_cost": 7, "target_segment": "inactive"}, sort_order=4),
            make_item(slug="booster-m", title="Booster M", description="Increase LMN rewards by 25% for your next 5 mission completions.", price=7, kind=StoreItemKind.boost, meta={"boost_pct": 25, "boost_missions": 5, "tags": ["entry", "boost"], "synergy_categories": ["progress", "spend"], "upgrade_track": "booster-core", "upgrade_tier": 2, "max_tier": 3, "next_upgrade_cost": 8, "target_segment": "balanced"}, sort_order=5),
            make_item(slug="booster-l", title="Booster L", description="Increase LMN rewards by 30% for your next 6 mission completions.", price=8, kind=StoreItemKind.boost, meta={"boost_pct": 30, "boost_missions": 6, "tags": ["entry", "best_value", "boost"], "synergy_categories": ["progress", "spend"], "upgrade_track": "booster-core", "upgrade_tier": 3, "max_tier": 3, "target_segment": "hoarder"}, sort_order=6),
            make_item(slug="weekend-premium-pass", title="Premium Pass - 2 days", description="Unlock premium prompts for a short sprint and feel the value before a bigger spend.", price=12, kind=StoreItemKind.premium_pass, meta={"premium_days": 2, "tags": ["popular"], "synergy_categories": ["learning"]}, sort_order=7),
            make_item(slug="starter-checkout-discount", title="20% off first paid month", description="A core-tier discount that keeps your next upgrade within reach.", price=14, kind=StoreItemKind.subscription_discount, meta={"discount_percent": 20, "code_prefix": "BOOST", "tags": ["best_value"], "synergy_categories": ["spend"]}, sort_order=8),
            make_item(slug="pro-trial-pass", title="Pro Pass - 7 days", description="Unlock premium prompts for a full week without changing your subscription yet.", price=30, kind=StoreItemKind.premium_pass, meta={"premium_days": 7, "tags": ["popular"], "synergy_categories": ["learning"]}, sort_order=9),
            make_item(slug="first-month-discount", title="40% off first paid month", description="Trade Lumens for a personal discount code you can use on your next checkout.", price=45, kind=StoreItemKind.subscription_discount, meta={"discount_percent": 40, "code_prefix": "SAVE", "tags": ["best_value"], "synergy_categories": ["spend"]}, sort_order=12),
        ]

        for index, prompt in enumerate(premium_prompts[:2], start=10):
            defaults.append(make_item(slug=f"unlock-{prompt.slug}", title=f"Unlock: {prompt.title}", description="Permanent access to this premium prompt from your personal library.", price=18 + (index - 10) * 4, kind=StoreItemKind.premium_prompt_unlock, meta={"prompt_id": str(prompt.id), "prompt_slug": prompt.slug, "prompt_title": prompt.title, "synergy_categories": ["prompt"]}, sort_order=index))

        if premium_prompts:
            defaults.append(make_item(slug="prompt-power-pack", title="Premium Prompt Pack", description="Unlock a curated pack of premium prompts and keep them in your workflow forever.", price=42, kind=StoreItemKind.prompt_bundle, meta={"prompt_ids": [str(prompt.id) for prompt in premium_prompts], "prompt_slugs": [prompt.slug for prompt in premium_prompts], "prompt_titles": [prompt.title for prompt in premium_prompts], "tags": ["best_value"], "synergy_categories": ["prompt", "progress"], "upgrade_track": "bundle-track", "upgrade_tier": 1, "max_tier": 2}, sort_order=13))
        return defaults

    async def sync_default_items(self) -> list[StoreItem]:
        premium_prompts = await self._store.list_featured_premium_prompts(limit=3)
        defaults = self._build_default_items(premium_prompts)

        for item in defaults:
            existing = await self._store.get_item_by_slug(item.slug)
            if existing is None:
                inserted = await self._store.try_add_item(item)
                if inserted:
                    continue
                existing = await self._store.get_item_by_slug(item.slug)
                if existing is None:
                    continue
            existing.title = item.title
            existing.description = item.description
            existing.price = item.price
            existing.kind = item.kind
            existing.meta = item.meta
            existing.sort_order = item.sort_order
            existing.is_active = True
        await self._store.flush()
        return await self._store.list_active_items()


async def sync_default_store_catalog(store_repo: StoreRepository, wallet_repo: WalletRepository) -> list[StoreItem]:
    service = StoreService(store_repo, wallet_repo)
    return await service.sync_default_items()
