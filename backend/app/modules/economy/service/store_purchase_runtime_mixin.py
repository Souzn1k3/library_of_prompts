from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any
import uuid

from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, StoreItem, StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.economy.config.tuning import DEFAULT_PREMIUM_DAYS
from app.modules.economy.model.store import PurchaseResult
from app.modules.economy.service.experiment_service import economy_experiment_metadata


class StorePurchaseRuntimeMixin:
    async def purchase(self, *, user: User, item_slug: str, client_token: str | None = None) -> PurchaseResult:
        if client_token:
            existing = await self._find_purchase_by_client_token(user_id=user.id, client_token=client_token)
            if existing is not None:
                return await self._purchase_result_from_existing(user=user, existing=existing)

        item = await self._store.get_item_by_slug(item_slug)
        if item is None:
            await self._catalog.sync_default_items()
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

        if self._catalog.is_one_time_item(item):
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
        daily_offer_slugs = self._catalog.daily_offer_rotation(await self._store.list_active_items(), now=now)
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
        self._rewards.apply_item_reward_metadata(item=item, purchase_metadata=purchase_metadata)

        if item.kind == StoreItemKind.premium_pass:
            days = int((item.meta or {}).get("premium_days", DEFAULT_PREMIUM_DAYS))
            premium_until = await self._wallet.grant_premium_days(user, days)
            purchase_metadata["premium_until"] = premium_until.isoformat()

        first_purchase_reward = await self._grant_first_purchase_bonus_if_needed(
            user=user,
            item=item,
            had_purchase_before=had_purchase_before,
            purchase_metadata=purchase_metadata,
            now=now,
        )

        purchase = await self._store.try_create_purchase(
            user_id=user.id,
            item=item,
            price_paid=item.price,
            client_token=effective_client_token,
            meta=purchase_metadata,
        )
        if purchase is None:
            await self._store.rollback()
            raise AppError(
                code="store_purchase_conflict",
                message="Purchase already exists or is being processed.",
                status_code=409,
                message_key="errors.store_purchase_conflict",
            )

        locked_cashback_reward, cashback_amount = await self._create_locked_cashback_reward(
            user=user,
            item=item,
            purchase_id=purchase.id,
            now=now,
        )

        await self._apply_item_kind_rewards(
            user=user,
            item=item,
            purchase_id=purchase.id,
            now=now,
        )

        second_purchase_challenge_reward, challenge_state = await self._apply_second_purchase_challenge(
            user=user,
            item=item,
            purchase_id=purchase.id,
            now=now,
            purchase_metadata=purchase_metadata,
            experiment_meta=experiment_meta,
        )

        purchase.meta = purchase_metadata

        feedback = await self._catalog.build_action_feedback(user, previous_balance=previous_balance)
        if feedback.wallet is None:
            raise AppError(
                code="wallet_missing",
                message="Wallet could not be loaded.",
                status_code=500,
                message_key="errors.wallet_missing",
            )

        await self._record_store_purchase_analytics(
            user=user,
            purchase_id=purchase.id,
            item=item,
            experiment_meta=experiment_meta,
            previous_balance=previous_balance,
            balance_after=feedback.wallet.balance,
            is_limited_offer=is_limited_offer,
            is_dynamic_offer=is_dynamic_offer,
            segment=segment,
            cashback_amount=cashback_amount,
            challenge_state=challenge_state,
        )

        return PurchaseResult(
            purchase=await self._catalog.serialize_purchase(
                purchase,
                fallback_item=item,
                balance=feedback.wallet.balance,
            ),
            wallet=feedback.wallet,
            available_items=feedback.available_items,
            newly_affordable_items=feedback.newly_affordable_items,
            best_item=feedback.best_item,
            first_purchase_reward=first_purchase_reward,
            locked_cashback_reward=locked_cashback_reward,
            second_purchase_challenge_reward=second_purchase_challenge_reward,
        )

    async def _record_store_purchase_analytics(
        self,
        *,
        user: User,
        purchase_id: uuid.UUID,
        item: StoreItem,
        experiment_meta: dict[str, object],
        previous_balance: int,
        balance_after: int,
        is_limited_offer: bool,
        is_dynamic_offer: bool,
        segment: str,
        cashback_amount: int,
        challenge_state: str,
    ) -> None:
        if self._analytics is None:
            return
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.store_purchase_completed,
            user_id=user.id,
            metadata={
                **experiment_meta,
                "purchase_id": str(purchase_id),
                "item_slug": item.slug,
                "item_kind": item.kind.value,
                "price_lmn": int(item.price),
                "balance_before": int(previous_balance),
                "balance_after": int(balance_after),
                "is_limited_offer": is_limited_offer,
                "is_dynamic_offer": is_dynamic_offer,
                "segment": segment,
                "locked_cashback_amount": cashback_amount,
                "second_purchase_challenge_state": challenge_state,
            },
            context_page="/api/v1/store",
            context_feature="purchase",
            event_id=f"store_purchase_completed:{user.id}:{purchase_id}",
        )
