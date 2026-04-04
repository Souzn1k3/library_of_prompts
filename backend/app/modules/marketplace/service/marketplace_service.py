from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.core.client_tokens import candidate_scoped_tokens, scoped_client_token, scoped_or_random_token
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.tiers import is_staff
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
    PlanTier,
    Prompt,
    PromptAccessSource,
    PromptPaymentMethod,
    PromptPrice,
    PromptPurchase,
    PromptReview,
    PurchaseStatus,
    ReviewModerationStatus,
    SubscriptionStatus,
    User,
)
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.marketplace.model.marketplace import (
    CatalogAction,
    MarketplaceOverviewRead,
    MarketplacePayoutRead,
    PromptAccessRead,
    PromptCheckoutSessionRequest,
    PromptCheckoutSessionResponse,
    PromptLumenPurchaseRequest,
    PromptPriceRead,
    PromptPurchaseActionResponse,
    PromptPurchaseRead,
    PromptReviewReportWrite,
    PromptReviewListRead,
    PromptReviewRead,
    PromptReviewWrite,
    ReviewSort,
    SellerMarketplaceSummaryRead,
    TrustIndicatorRead,
)
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.payout_manager import MarketplacePayoutManager
from app.modules.marketplace.service.policy import (
    MARKETPLACE_COMMISSION_PERCENT,
    MAX_AUTHOR_REVIEWS_PER_24H,
    MAX_REVIEW_EDITS,
    REVIEW_EDIT_COOLDOWN_MINUTES,
    REVIEW_HIDE_REPORT_THRESHOLD,
    SUSPICIOUS_SELLER_REVIEW_THRESHOLD,
    append_query,
    apply_discount,
    ensure_aware,
    fee,
    normalize_prompt_price,
    price_lumens_from_rub,
    round_rating,
    settlement_available_at,
    start_of_current_month,
)

_stripe_module: Any | None
try:
    import stripe as _stripe_module
except Exception:  # pragma: no cover - runtime optional
    _stripe_module = None

stripe: Any = _stripe_module


@dataclass(slots=True)
class PlanAccessContext:
    total_unlocks: int = 0
    remaining_unlocks: int = 0
    money_discount_percent: int = 0
    lumen_discount_percent: int = 0


class MarketplaceService:
    def __init__(
        self,
        repo: MarketplaceRepository,
        billing_repo: BillingRepository,
        wallet_repo: WalletRepository,
        store_repo: StoreRepository,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._billing = billing_repo
        self._wallet = wallet_repo
        self._store = store_repo
        self._settings = settings
        self._payouts = MarketplacePayoutManager(repo, wallet_repo)

    def _seller_amount_for_currency(self, purchase: PromptPurchase, currency_code: str) -> int:
        return self._payouts.seller_amount_for_currency(purchase, currency_code)

    def _payout_to_read(self, payout: MarketplacePayout) -> MarketplacePayoutRead:
        return self._payouts.payout_to_read(payout)

    def _review_is_public(self, review: PromptReview) -> bool:
        return review.is_visible and review.moderation_status == ReviewModerationStatus.visible

    def _initial_settlement_status(
        self,
        *,
        seller_amount_rub: int,
        seller_amount_lumens: int,
        completed_at: datetime,
    ) -> tuple[MarketplaceSettlementStatus, datetime | None]:
        if seller_amount_rub <= 0 and seller_amount_lumens <= 0:
            return MarketplaceSettlementStatus.available, completed_at
        return MarketplaceSettlementStatus.pending, settlement_available_at(completed_at)

    def _redirect_origin(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if not parsed.hostname or parsed.username or parsed.password:
            return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme.lower() == "https" else 80
        return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}:{port}"

    def _allowed_checkout_redirect_origins(self) -> set[str]:
        urls = list(self._settings.cors_origin_list)
        urls.extend(
            [
                self._settings.billing_checkout_success_url,
                self._settings.billing_checkout_cancel_url,
                self._settings.billing_portal_return_url,
            ]
        )
        out: set[str] = set()
        for url in urls:
            origin = self._redirect_origin(url)
            if origin:
                out.add(origin)
        return out

    def _resolve_checkout_redirect_url(self, candidate: str | None, *, default_url: str) -> str:
        raw = (candidate or "").strip()
        if not raw:
            return default_url

        parsed = urlparse(raw)
        if not parsed.scheme and not parsed.netloc:
            if not raw.startswith("/") or raw.startswith("//"):
                raise AppError(
                    code="invalid_redirect_url",
                    status_code=400,
                    message="This redirect URL is not allowed.",
                )
            raw = urljoin(default_url, raw)

        origin = self._redirect_origin(raw)
        if origin is None or origin not in self._allowed_checkout_redirect_origins():
            raise AppError(
                code="invalid_redirect_url",
                status_code=400,
                message="This redirect URL is not allowed.",
            )
        return raw

    def _normalize_payout_currency(self, currency_code: str) -> str:
        return self._payouts.normalize_payout_currency(currency_code)

    def _client_token_scope(self, user_id: uuid.UUID, client_token: str, *, prefix: str) -> str:
        return scoped_client_token(user_id, client_token, prefix=prefix)

    def _scoped_client_token(self, user_id: uuid.UUID, client_token: str | None, *, prefix: str) -> str:
        return scoped_or_random_token(user_id, client_token, prefix=prefix)

    def _candidate_client_tokens(self, user_id: uuid.UUID, client_token: str, *, prefix: str) -> list[str]:
        return candidate_scoped_tokens(user_id, client_token, prefix=prefix)

    async def _find_purchase_by_client_token(
        self,
        *,
        user_id: uuid.UUID,
        client_token: str,
        prefix: str,
    ) -> PromptPurchase | None:
        for token in self._candidate_client_tokens(user_id, client_token, prefix=prefix):
            purchase = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=token)
            if purchase is not None:
                return purchase
        return None

    def _eligible_payout_purchases(self, payout: MarketplacePayout) -> list[PromptPurchase]:
        return self._payouts.eligible_payout_purchases(payout)

    async def _sync_reserved_payout(self, payout: MarketplacePayout) -> MarketplacePayout:
        return await self._payouts.sync_reserved_payout(payout)

    async def _release_payout_reservations(self, payout: MarketplacePayout) -> None:
        await self._payouts.release_payout_reservations(payout)

    def _price_to_read(self, price: PromptPrice | None) -> PromptPriceRead | None:
        if price is None or not price.is_active:
            return None
        return PromptPriceRead(
            price_rub=price.price_rub,
            price_lumens=price.price_lumens,
            commission_percent=price.commission_percent,
        )

    def _review_to_read(self, review: PromptReview, prompt: Prompt, author: User, author_slug: str | None) -> PromptReviewRead:
        return PromptReviewRead(
            id=review.id,
            rating=review.rating,
            text=review.body,
            author_user_id=author.id,
            author_display_name=author.display_name,
            author_slug=author_slug,
            prompt_id=prompt.id,
            prompt_slug=prompt.slug,
            prompt_title=prompt.title,
            created_at=review.created_at,
            updated_at=review.updated_at,
            verified_purchase=True,
            moderation_status=review.moderation_status,
            moderation_reason=review.moderation_reason,
            reported_count=review.reported_count,
        )

    def _purchase_to_read(self, purchase: PromptPurchase, *, can_review: bool | None = None) -> PromptPurchaseRead:
        prompt = purchase.prompt
        if prompt is None:
            raise AppError(code="prompt_missing", message="Purchase prompt details are unavailable.", status_code=500)
        review_read: PromptReviewRead | None = None
        purchase_state = sa_inspect(purchase)
        review = purchase.review if "review" not in purchase_state.unloaded else None
        if review is not None:
            review_state = sa_inspect(review)
            author = review.author if "author" not in review_state.unloaded else None
        else:
            author = None
        if review is not None and author is not None:
            author_slug = (
                author.contributor_profile.slug
                if author.contributor_profile is not None
                else None
            )
            review_read = self._review_to_read(review, prompt, author, author_slug)
        return PromptPurchaseRead(
            id=purchase.id,
            prompt_id=purchase.prompt_id,
            prompt_slug=prompt.slug,
            prompt_title=prompt.title,
            seller_user_id=purchase.seller_user_id,
            status=purchase.status,
            payment_method=purchase.payment_method,
            price_rub=purchase.price_rub,
            price_lumens=purchase.price_lumens,
            settlement_status=purchase.settlement_status,
            settlement_available_at=purchase.settlement_available_at,
            paid_out_at=purchase.paid_out_at,
            created_at=purchase.created_at,
            completed_at=purchase.completed_at,
            can_review=can_review if can_review is not None else purchase.status == PurchaseStatus.completed,
            review=review_read,
        )

    def _trust_indicators(
        self,
        *,
        review_count: int,
        rating_average: float | None,
        sold_prompts_count: int,
        reputation_tier: str | None,
    ) -> list[TrustIndicatorRead]:
        indicators: list[TrustIndicatorRead] = []
        if reputation_tier in {"verified", "top"}:
            indicators.append(TrustIndicatorRead(key="verified_creator", level="good"))
        if reputation_tier == "top":
            indicators.append(TrustIndicatorRead(key="top_contributor", level="strong"))
        if review_count >= 5 and rating_average is not None and rating_average >= 4.6:
            indicators.append(TrustIndicatorRead(key="high_rating", level="strong"))
        if sold_prompts_count >= 10:
            indicators.append(TrustIndicatorRead(key="top_seller", level="good"))
        if not indicators:
            indicators.append(TrustIndicatorRead(key="new_marketplace_profile", level="info"))
        return indicators

    async def get_prompt_or_404(self, prompt_id: uuid.UUID) -> Prompt:
        prompt = await self._repo.get_prompt_by_id(prompt_id)
        if prompt is None:
            raise NotFoundError("prompt", str(prompt_id))
        return prompt

    async def refresh_settlement_states(
        self,
        *,
        seller_user_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> int:
        return await self._payouts.refresh_settlement_states(
            seller_user_id=seller_user_id,
            now=now,
        )

    async def create_payout_batch(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        notes: str | None = None,
    ) -> MarketplacePayoutRead:
        return await self._payouts.create_payout_batch(
            seller_user_id=seller_user_id,
            currency_code=currency_code,
            notes=notes,
        )

    async def mark_payout_processing(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.mark_payout_processing(payout_id=payout_id)

    async def fail_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.fail_payout(payout_id=payout_id)

    async def cancel_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        return await self._payouts.cancel_payout(payout_id=payout_id)

    async def finalize_payout(
        self,
        *,
        payout_id: uuid.UUID,
        reference: str | None = None,
        now: datetime | None = None,
    ) -> MarketplacePayoutRead:
        return await self._payouts.finalize_payout(
            payout_id=payout_id,
            reference=reference,
            now=now,
        )

    async def _resolve_usage_window(self, *, user_id: uuid.UUID, plan_tier: PlanTier) -> tuple[datetime, datetime]:
        latest = await self._billing.get_latest_subscription_for_user(user_id)
        if (
            latest is not None
            and latest.plan is not None
            and latest.plan.tier == plan_tier
            and latest.status in {SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due}
        ):
            start = ensure_aware(latest.current_period_start)
            end = ensure_aware(latest.current_period_end)
            if start is not None and end is not None and end > start:
                return start, end
        return start_of_current_month(datetime.now(timezone.utc))

    async def _get_or_create_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        for_update: bool,
    ):
        usage = await self._repo.get_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        if usage is not None:
            return usage

        plan = await self._billing.get_plan_by_tier(plan_tier)
        included_limit = int(plan.monthly_paid_prompt_limit) if plan is not None else 0
        created = await self._repo.try_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_limit,
        )
        if created is not None:
            return created
        usage = await self._repo.get_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        if usage is None:
            raise RuntimeError("Plan usage window insert conflicted but row was not found.")
        return usage

    async def _get_plan_access_context(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        for_update: bool = False,
    ) -> PlanAccessContext:
        plan = await self._billing.get_plan_by_tier(plan_tier)
        if plan is None:
            return PlanAccessContext()
        total_unlocks = int(plan.monthly_paid_prompt_limit or 0)
        money_discount_percent = int(plan.prompt_purchase_discount_percent or 0)
        lumen_discount_percent = int(plan.lumen_purchase_discount_percent or 0)
        window_started_at, window_ends_at = await self._resolve_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
        )
        usage = await self._get_or_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        used = int(usage.used_paid_prompt_unlocks or 0)
        return PlanAccessContext(
            total_unlocks=total_unlocks,
            remaining_unlocks=max(total_unlocks - used, 0),
            money_discount_percent=money_discount_percent,
            lumen_discount_percent=lumen_discount_percent,
        )

    async def get_plan_access_context(self, user: User, *, for_update: bool = False) -> PlanAccessContext:
        return await self._get_plan_access_context(
            user_id=user.id,
            plan_tier=user.plan_tier,
            for_update=for_update,
        )

    async def build_access_map(self, rows: list[Prompt], viewer: User | None) -> dict[uuid.UUID, PromptAccessRead]:
        if not rows:
            return {}
        prompt_ids = [row.id for row in rows]
        prices = await self._repo.list_prompt_prices(prompt_ids)
        if viewer is None:
            return {
                row.id: PromptAccessRead(
                    has_access=False,
                    purchase_required=True,
                    catalog_action=CatalogAction.signin,
                )
                for row in rows
                if prices.get(row.id) is not None and prices[row.id].is_active
            }
        entitled_ids = await self._repo.list_entitled_prompt_ids(user_id=viewer.id, prompt_ids=prompt_ids)
        legacy_owned_ids = await self._store.list_owned_prompt_ids(user_id=viewer.id, prompt_ids=prompt_ids)
        plan_context = await self.get_plan_access_context(viewer)
        out: dict[uuid.UUID, PromptAccessRead] = {}
        for row in rows:
            price = prices.get(row.id)
            if price is None or not price.is_active:
                continue
            if row.author_id == viewer.id:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.author.value)
                continue
            if is_staff(viewer):
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.staff.value)
                continue
            if row.id in entitled_ids:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                continue
            if row.id in legacy_owned_ids:
                out[row.id] = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.legacy_store.value)
                continue
            if plan_context.remaining_unlocks > 0:
                out[row.id] = PromptAccessRead(
                    has_access=False,
                    can_unlock_with_plan=True,
                    remaining_plan_unlocks=plan_context.remaining_unlocks,
                    monthly_plan_unlocks=plan_context.total_unlocks,
                    catalog_action=CatalogAction.open,
                )
            else:
                out[row.id] = PromptAccessRead(
                    has_access=False,
                    purchase_required=True,
                    monthly_plan_unlocks=plan_context.total_unlocks,
                    catalog_action=CatalogAction.buy,
                )
        return out

    async def resolve_prompt_access(
        self,
        prompt: Prompt,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = False,
    ) -> PromptAccessRead:
        price = prompt.pricing
        if price is None or not price.is_active:
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.free.value)
        if viewer is None:
            return PromptAccessRead(
                has_access=False,
                purchase_required=True,
                catalog_action=CatalogAction.signin,
            )
        viewer_id = viewer.id
        viewer_plan_tier = viewer.plan_tier
        if prompt.author_id == viewer_id:
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.author.value)
        prompt_id = prompt.id
        seller_user_id = prompt.author_id
        if is_staff(viewer):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.staff.value)
        entitlement = await self._repo.get_entitlement(
            user_id=viewer_id,
            prompt_id=prompt_id,
            for_update=auto_grant_included_unlock,
        )
        if entitlement is not None:
            return PromptAccessRead(has_access=True, is_owned=True, source=entitlement.source.value)
        if await self._store.user_has_prompt_access(user_id=viewer_id, prompt_id=prompt_id):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.legacy_store.value)
        plan_context = await self._get_plan_access_context(
            user_id=viewer_id,
            plan_tier=viewer_plan_tier,
            for_update=auto_grant_included_unlock,
        )
        if plan_context.remaining_unlocks <= 0:
            return PromptAccessRead(
                has_access=False,
                purchase_required=True,
                remaining_plan_unlocks=0,
                monthly_plan_unlocks=plan_context.total_unlocks,
                catalog_action=CatalogAction.buy,
            )
        if not auto_grant_included_unlock:
            return PromptAccessRead(
                has_access=False,
                can_unlock_with_plan=True,
                remaining_plan_unlocks=plan_context.remaining_unlocks,
                monthly_plan_unlocks=plan_context.total_unlocks,
                    catalog_action=CatalogAction.open,
                )
        await self._grant_included_unlock(
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            user_id=viewer_id,
            plan_tier=viewer_plan_tier,
            plan_context=plan_context,
        )
        return PromptAccessRead(
            has_access=True,
            is_owned=True,
            source=PromptAccessSource.subscription_limit.value,
            can_unlock_with_plan=True,
            remaining_plan_unlocks=max(plan_context.remaining_unlocks - 1, 0),
            monthly_plan_unlocks=plan_context.total_unlocks,
        )

    async def _grant_included_unlock(
        self,
        *,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        plan_context: PlanAccessContext,
    ) -> PromptPurchase:
        if plan_context.remaining_unlocks <= 0:
            raise AppError(
                code="plan_unlocks_exhausted",
                message="You've used all included paid prompt unlocks for the current period.",
                status_code=402,
            )
        window_started_at, window_ends_at = await self._resolve_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
        )
        usage = await self._get_or_create_plan_usage_window(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=True,
        )
        if usage.used_paid_prompt_unlocks >= usage.included_paid_prompt_limit:
            raise AppError(
                code="plan_unlocks_exhausted",
                message="You've used all included paid prompt unlocks for the current period.",
                status_code=402,
            )
        plan_token = f"plan-{user_id}-{prompt_id}"
        now = datetime.now(timezone.utc)
        created_purchase = True
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.included_limit,
            status=PurchaseStatus.completed,
            settlement_status=MarketplaceSettlementStatus.available,
            price_rub=0,
            price_lumens=0,
            client_token=plan_token,
            settlement_available_at=now,
            completed_at=now,
            meta={"included_unlock": True, "plan_tier": plan_tier.value},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=plan_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                created_purchase = False
                purchase = existing
            else:
                raise RuntimeError("Included unlock purchase insert conflicted but existing row was not found.")

        entitlement = await self._repo.try_create_entitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=PromptAccessSource.subscription_limit,
            purchase_id=purchase.id,
            meta={"plan_tier": plan_tier.value},
            granted_at=now,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id, for_update=True)
            if entitlement is None:
                raise

        # Idempotency guard: retried/concurrent unlock requests that resolve to an existing
        # purchase+entitlement must not consume included quota twice.
        if not created_purchase or entitlement.purchase_id != purchase.id:
            return purchase

        usage.used_paid_prompt_unlocks += 1
        await self._repo.save_plan_usage_window(usage)
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt_id,
            actor_user_id=user_id,
            kind=MarketplaceTransactionKind.included_unlock,
            currency_code="PLAN",
            amount=1,
            meta={"plan_tier": plan_tier.value},
        )
        return purchase

    async def upsert_prompt_price(self, prompt: Prompt, price_rub: int | None) -> PromptPrice | None:
        prompt_state = sa_inspect(prompt)
        pricing = prompt.pricing if "pricing" not in prompt_state.unloaded else await self._repo.get_prompt_price(prompt.id)
        normalized = normalize_prompt_price(price_rub)
        if normalized is None:
            if pricing is not None:
                pricing.is_active = False
            prompt.is_premium = False
            return pricing
        price_rub_value, price_lumens_value = normalized
        if pricing is None:
            pricing = PromptPrice(
                prompt_id=prompt.id,
                price_rub=price_rub_value,
                price_lumens=price_lumens_value,
                commission_percent=MARKETPLACE_COMMISSION_PERCENT,
                is_active=True,
            )
            prompt.pricing = pricing
        else:
            pricing.price_rub = price_rub_value
            pricing.price_lumens = price_lumens_value
            pricing.commission_percent = MARKETPLACE_COMMISSION_PERCENT
            pricing.is_active = True
        prompt.is_premium = True
        return pricing

    async def purchase_with_lumens(
        self,
        *,
        user: User,
        prompt: Prompt,
        payload: PromptLumenPurchaseRequest,
    ) -> PromptPurchaseActionResponse:
        token_prefix = "mkt-lmn"
        user_id = user.id
        staff_user = is_staff(user)
        prompt_id = prompt.id
        seller_user_id = prompt.author_id
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        base_price_lumens = int(prompt.pricing.price_lumens)
        if seller_user_id == user_id:
            raise AppError(code="cannot_buy_own_prompt", message="You can't buy your own prompt.", status_code=400)
        if staff_user:
            raise ConflictError("You already own this prompt.")
        entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id)
        if entitlement is not None or await self._store.user_has_prompt_access(user_id=user_id, prompt_id=prompt_id):
            raise ConflictError("You already own this prompt.")

        if payload.client_token:
            existing = await self._find_purchase_by_client_token(
                user_id=user_id,
                client_token=payload.client_token,
                prefix=token_prefix,
            )
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                return PromptPurchaseActionResponse(purchase=self._purchase_to_read(existing), access=access)

        active_purchase = await self._repo.get_active_purchase(user_id=user_id, prompt_id=prompt_id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")

        effective_client_token = self._scoped_client_token(user_id, payload.client_token, prefix=token_prefix)
        plan_context = await self.get_plan_access_context(user)
        effective_price_lumens = apply_discount(base_price_lumens, plan_context.lumen_discount_percent)
        fee_lumens = fee(effective_price_lumens)
        seller_lumens = max(effective_price_lumens - fee_lumens, 0)
        now = datetime.now(timezone.utc)
        settlement_status, settlement_available_at = self._initial_settlement_status(
            seller_amount_rub=0,
            seller_amount_lumens=seller_lumens,
            completed_at=now,
        )
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.lumens,
            status=PurchaseStatus.pending,
            settlement_status=settlement_status,
            price_rub=0,
            price_lumens=effective_price_lumens,
            platform_fee_lumens=fee_lumens,
            seller_amount_lumens=seller_lumens,
            settlement_available_at=settlement_available_at,
            client_token=effective_client_token,
            meta={"base_price_lumens": base_price_lumens},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
                return PromptPurchaseActionResponse(purchase=self._purchase_to_read(existing), access=access)
            raise ConflictError("A purchase for this prompt is already being processed.")
        prompt_row = await self._repo.get_prompt_by_id(prompt_id)
        if prompt_row is not None:
            purchase.prompt = prompt_row
        await self._wallet.adjust_balance(
            user_id=user_id,
            amount=-effective_price_lumens,
            reason=CurrencyTransactionType.marketplace_purchase,
            context=f"prompt:{prompt_id}:purchase:{purchase.id}:buyer",
            source_id=purchase.id,
            metadata={"prompt_id": str(prompt_id), "purchase_id": str(purchase.id)},
            now=now,
        )
        purchase.status = PurchaseStatus.completed
        purchase.completed_at = now
        await self._repo.save_purchase(purchase)
        entitlement = await self._repo.try_create_entitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=PromptAccessSource.direct_lumens,
            purchase_id=purchase.id,
            meta={"payment_method": PromptPaymentMethod.lumens.value},
            granted_at=now,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id, for_update=True)
            if entitlement is None:
                raise
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt_id,
            actor_user_id=user_id,
            kind=MarketplaceTransactionKind.buyer_charge,
            currency_code="LMN",
            amount=effective_price_lumens,
            meta={"prompt_id": str(prompt_id)},
        )
        if seller_user_id is not None and seller_lumens > 0:
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt_id,
                actor_user_id=seller_user_id,
                kind=MarketplaceTransactionKind.seller_credit,
                currency_code="LMN",
                amount=seller_lumens,
                meta={"prompt_id": str(prompt_id)},
            )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt_id,
            actor_user_id=None,
            kind=MarketplaceTransactionKind.platform_fee,
            currency_code="LMN",
            amount=fee_lumens,
            meta={"prompt_id": str(prompt_id)},
        )
        access = PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.direct_lumens.value)
        return PromptPurchaseActionResponse(
            purchase=self._purchase_to_read(purchase, can_review=True),
            access=access,
        )

    def _stripe_checkout_enabled(self) -> bool:
        return bool(stripe and self._settings.stripe_secret_key)

    async def create_checkout_session(
        self,
        *,
        user: User,
        payload: PromptCheckoutSessionRequest,
    ) -> PromptCheckoutSessionResponse:
        token_prefix = "mkt-checkout"
        user_id = user.id
        staff_user = is_staff(user)
        prompt = await self._repo.get_prompt_by_id(payload.prompt_id)
        if prompt is None:
            raise NotFoundError("prompt", str(payload.prompt_id))
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        prompt_id = prompt.id
        prompt_slug = prompt.slug
        prompt_title = prompt.title
        prompt_summary = prompt.summary or "Paid prompt unlock"
        seller_user_id = prompt.author_id
        base_price_rub = int(prompt.pricing.price_rub)
        if seller_user_id == user_id:
            raise AppError(code="cannot_buy_own_prompt", message="You can't buy your own prompt.", status_code=400)
        if staff_user:
            raise ConflictError("You already own this prompt.")
        entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id)
        if entitlement is not None or await self._store.user_has_prompt_access(user_id=user_id, prompt_id=prompt_id):
            raise ConflictError("You already own this prompt.")
        if payload.client_token:
            existing = await self._find_purchase_by_client_token(
                user_id=user_id,
                client_token=payload.client_token,
                prefix=token_prefix,
            )
            if existing is not None and existing.status == PurchaseStatus.completed:
                raise ConflictError("This prompt is already purchased.")
        active_purchase = await self._repo.get_active_purchase(user_id=user_id, prompt_id=prompt_id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")
        effective_client_token = self._scoped_client_token(user_id, payload.client_token, prefix=token_prefix)
        plan_context = await self.get_plan_access_context(user)
        effective_price_rub = apply_discount(base_price_rub, plan_context.money_discount_percent)
        fee_rub = fee(effective_price_rub)
        seller_rub = max(effective_price_rub - fee_rub, 0)
        purchase = await self._repo.try_create_purchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=PromptPaymentMethod.stripe,
            status=PurchaseStatus.pending,
            price_rub=effective_price_rub,
            price_lumens=0,
            platform_fee_rub=fee_rub,
            seller_amount_rub=seller_rub,
            client_token=effective_client_token,
            meta={"base_price_rub": base_price_rub},
        )
        if purchase is None:
            existing = await self._repo.get_purchase_by_client_token(user_id=user_id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                raise ConflictError("This prompt is already purchased.")
            raise ConflictError("A purchase for this prompt is already being processed.")
        success_url = self._resolve_checkout_redirect_url(
            payload.success_url,
            default_url=append_query(self._settings.billing_checkout_success_url, prompt=prompt_slug),
        )
        cancel_url = self._resolve_checkout_redirect_url(
            payload.cancel_url,
            default_url=self._settings.billing_checkout_cancel_url,
        )
        if self._settings.billing_mock_mode or not self._stripe_checkout_enabled():
            completed_at = datetime.now(timezone.utc)
            settlement_status, settlement_available_at = self._initial_settlement_status(
                seller_amount_rub=seller_rub,
                seller_amount_lumens=0,
                completed_at=completed_at,
            )
            purchase.status = PurchaseStatus.completed
            purchase.completed_at = completed_at
            purchase.settlement_status = settlement_status
            purchase.settlement_available_at = settlement_available_at
            purchase.meta = {**(purchase.meta or {}), "mock": True}
            await self._repo.save_purchase(purchase)
            entitlement = await self._repo.try_create_entitlement(
                user_id=user_id,
                prompt_id=prompt_id,
                source=PromptAccessSource.direct_money,
                purchase_id=purchase.id,
                meta={"payment_method": PromptPaymentMethod.stripe.value, "mock": True},
                granted_at=completed_at,
            )
            if entitlement is None:
                entitlement = await self._repo.get_entitlement(user_id=user_id, prompt_id=prompt_id, for_update=True)
                if entitlement is None:
                    raise
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt_id,
                actor_user_id=user_id,
                kind=MarketplaceTransactionKind.buyer_charge,
                currency_code="RUB",
                amount=effective_price_rub,
                meta={"prompt_id": str(prompt_id), "mock": True},
            )
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt_id,
                actor_user_id=None,
                kind=MarketplaceTransactionKind.platform_fee,
                currency_code="RUB",
                amount=fee_rub,
                meta={"prompt_id": str(prompt_id), "mock": True},
            )
            if seller_user_id is not None and seller_rub > 0:
                await self._repo.create_marketplace_transaction(
                    prompt_purchase_id=purchase.id,
                    prompt_id=prompt_id,
                    actor_user_id=seller_user_id,
                    kind=MarketplaceTransactionKind.seller_credit,
                    currency_code="RUB",
                    amount=seller_rub,
                    meta={"prompt_id": str(prompt_id), "mock": True},
                )
            return PromptCheckoutSessionResponse(
                url=success_url,
                session_id=f"mock_prompt_{purchase.id.hex}",
                purchase_id=purchase.id,
            )
        assert stripe is not None
        stripe.api_key = self._settings.stripe_secret_key
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "rub",
                        "unit_amount": effective_price_rub * 100,
                        "product_data": {
                            "name": prompt_title,
                            "description": prompt_summary,
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user_id),
            metadata={
                "kind": "prompt_purchase",
                "purchase_id": str(purchase.id),
                "prompt_id": str(prompt_id),
                "user_id": str(user_id),
            },
            payment_intent_data={
                "metadata": {
                    "kind": "prompt_purchase",
                    "purchase_id": str(purchase.id),
                    "prompt_id": str(prompt_id),
                    "user_id": str(user_id),
                }
            },
        )
        purchase.provider_checkout_id = str(getattr(session, "id", None) or session.get("id"))
        await self._repo.save_purchase(purchase)
        return PromptCheckoutSessionResponse(
            url=str(getattr(session, "url", None) or session.get("url")),
            session_id=purchase.provider_checkout_id,
            purchase_id=purchase.id,
        )

    async def complete_checkout_purchase(
        self,
        *,
        checkout_id: str,
        payment_id: str | None = None,
        completed_at: datetime | None = None,
    ) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_checkout_id(checkout_id)
        if purchase is None:
            return None
        if purchase.status == PurchaseStatus.completed:
            return purchase
        completed_at = completed_at or datetime.now(timezone.utc)
        settlement_status, settlement_available_at = self._initial_settlement_status(
            seller_amount_rub=purchase.seller_amount_rub,
            seller_amount_lumens=0,
            completed_at=completed_at,
        )
        purchase.status = PurchaseStatus.completed
        purchase.provider_payment_id = payment_id or purchase.provider_payment_id
        purchase.completed_at = completed_at
        purchase.settlement_status = settlement_status
        purchase.settlement_available_at = settlement_available_at
        await self._repo.save_purchase(purchase)
        entitlement = await self._repo.try_create_entitlement(
            user_id=purchase.user_id,
            prompt_id=purchase.prompt_id,
            source=PromptAccessSource.direct_money,
            purchase_id=purchase.id,
            meta={"payment_method": PromptPaymentMethod.stripe.value},
            granted_at=completed_at,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(
                user_id=purchase.user_id,
                prompt_id=purchase.prompt_id,
                for_update=True,
            )
            if entitlement is None:
                raise
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=purchase.prompt_id,
            actor_user_id=purchase.user_id,
            kind=MarketplaceTransactionKind.buyer_charge,
            currency_code="RUB",
            amount=purchase.price_rub,
            meta={"purchase_id": str(purchase.id)},
        )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=purchase.prompt_id,
            actor_user_id=None,
            kind=MarketplaceTransactionKind.platform_fee,
            currency_code="RUB",
            amount=purchase.platform_fee_rub,
            meta={"purchase_id": str(purchase.id)},
        )
        if purchase.seller_user_id is not None and purchase.seller_amount_rub > 0:
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_credit,
                currency_code="RUB",
                amount=purchase.seller_amount_rub,
                meta={"purchase_id": str(purchase.id)},
            )
        return purchase

    async def fail_checkout_purchase(self, *, checkout_id: str, reason: str) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_checkout_id(checkout_id)
        if purchase is None or purchase.status != PurchaseStatus.pending:
            return purchase
        purchase.status = PurchaseStatus.failed
        purchase.meta = {**(purchase.meta or {}), "failure_reason": reason}
        await self._repo.save_purchase(purchase)
        return purchase

    async def fail_checkout_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_id(purchase_id)
        if purchase is None or purchase.status != PurchaseStatus.pending:
            return purchase
        purchase.status = PurchaseStatus.failed
        purchase.meta = {**(purchase.meta or {}), "failure_reason": reason}
        await self._repo.save_purchase(purchase)
        return purchase

    async def refund_purchase_by_id(self, *, purchase_id: uuid.UUID, reason: str | None = None) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_id(purchase_id, for_update=True)
        if purchase is None:
            return None
        return await self._refund_purchase(purchase=purchase, reason=reason)

    async def refund_checkout_purchase(self, *, payment_id: str, reason: str | None = None) -> PromptPurchase | None:
        purchase = await self._repo.get_purchase_by_provider_payment_id(payment_id)
        if purchase is None:
            return purchase
        return await self._refund_purchase(purchase=purchase, reason=reason)

    async def _refund_purchase(self, *, purchase: PromptPurchase, reason: str | None = None) -> PromptPurchase:
        if purchase.status == PurchaseStatus.refunded:
            return purchase
        now = datetime.now(timezone.utc)
        prior_settlement_status = purchase.settlement_status
        payout = None
        if purchase.payout_id is not None:
            payout = await self._repo.get_payout_by_id(purchase.payout_id, for_update=True)
        purchase.status = PurchaseStatus.refunded
        purchase.settlement_status = MarketplaceSettlementStatus.refunded
        purchase.refunded_at = now
        purchase.meta = {
            **(purchase.meta or {}),
            "refund_reason": reason,
            "prior_settlement_status": prior_settlement_status.value,
        }
        await self._repo.save_purchase(purchase)
        if payout is not None and payout.status in {MarketplacePayoutStatus.requested, MarketplacePayoutStatus.processing}:
            await self._sync_reserved_payout(payout)
        entitlement = await self._repo.get_entitlement(user_id=purchase.user_id, prompt_id=purchase.prompt_id, for_update=True)
        if entitlement is not None:
            entitlement.revoked_at = now
            entitlement.revoke_reason = reason or "refunded"
            await self._repo.save_entitlement(entitlement)
        review = await self._repo.get_review_by_purchase_id(purchase.id)
        if review is not None:
            review.is_visible = False
            review.moderation_status = ReviewModerationStatus.hidden
            review.moderation_reason = "refunded_purchase"
            review.hidden_at = now
            await self._repo.save_review(review)

        if purchase.price_lumens > 0:
            await self._wallet.adjust_balance(
                user_id=purchase.user_id,
                amount=purchase.price_lumens,
                reason=CurrencyTransactionType.refund,
                context=f"prompt:{purchase.prompt_id}:purchase:{purchase.id}:buyer_refund",
                source_id=purchase.id,
                metadata={"purchase_id": str(purchase.id), "reason": reason, "currency_code": "LMN"},
                now=now,
            )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=purchase.prompt_id,
            actor_user_id=purchase.user_id,
            kind=MarketplaceTransactionKind.refund,
            currency_code="LMN" if purchase.price_lumens > 0 else "RUB",
            amount=max(purchase.price_lumens, purchase.price_rub),
            meta={"purchase_id": str(purchase.id), "reason": reason},
        )
        if purchase.seller_user_id is not None and (purchase.seller_amount_rub > 0 or purchase.seller_amount_lumens > 0):
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_reversal,
                currency_code="LMN" if purchase.seller_amount_lumens > 0 else "RUB",
                amount=max(purchase.seller_amount_lumens, purchase.seller_amount_rub),
                meta={
                    "purchase_id": str(purchase.id),
                    "reason": reason,
                    "prior_settlement_status": prior_settlement_status.value,
                },
            )
        return purchase

    async def report_review(
        self,
        *,
        user: User,
        review_id: uuid.UUID,
        payload: PromptReviewReportWrite,
    ) -> PromptReviewRead:
        review = await self._repo.get_review_by_id(review_id)
        if review is None:
            raise NotFoundError("prompt_review", str(review_id))
        if review.author_user_id == user.id:
            raise AppError(code="cannot_report_own_review", message="You can't report your own review.", status_code=400)
        try:
            await self._repo.create_review_report(
                review_id=review.id,
                reporter_user_id=user.id,
                reason=payload.reason.strip().lower(),
                details=payload.details.strip() if payload.details else None,
            )
        except IntegrityError as exc:
            raise ConflictError("You already reported this review.") from exc
        review.reported_count = await self._repo.count_review_reports(review.id)
        review.last_reported_at = datetime.now(timezone.utc)
        if review.reported_count >= REVIEW_HIDE_REPORT_THRESHOLD:
            review.is_visible = False
            review.moderation_status = ReviewModerationStatus.hidden
            review.moderation_reason = "reported_by_users"
            review.hidden_at = review.last_reported_at
        await self._repo.save_review(review)
        author_slug = review.author.contributor_profile.slug if review.author and review.author.contributor_profile else None
        assert review.prompt is not None and review.author is not None
        return self._review_to_read(review, review.prompt, review.author, author_slug)

    async def _review_moderation_state(
        self,
        *,
        author_user_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        review_text: str | None,
        existing_review: PromptReview | None = None,
    ) -> tuple[ReviewModerationStatus, str | None]:
        normalized_text = review_text.strip() if review_text else ""
        if existing_review is not None and existing_review.edit_count >= MAX_REVIEW_EDITS:
            raise AppError(
                code="review_edit_limit_reached",
                message="This review has reached the edit limit.",
                status_code=409,
            )
        if existing_review is not None and existing_review.updated_at is not None:
            cooldown_until = existing_review.updated_at + timedelta(minutes=REVIEW_EDIT_COOLDOWN_MINUTES)
            if datetime.now(timezone.utc) < cooldown_until:
                raise AppError(
                    code="review_edit_cooldown",
                    message="Please wait a bit before editing this review again.",
                    status_code=429,
                )
        recent_reviews = await self._repo.count_recent_reviews_by_author(author_user_id=author_user_id, hours=24)
        if recent_reviews >= MAX_AUTHOR_REVIEWS_PER_24H:
            return ReviewModerationStatus.pending, "review_velocity"
        same_seller_reviews = await self._repo.count_reviews_for_seller_by_author(
            seller_user_id=seller_user_id,
            author_user_id=author_user_id,
        )
        if same_seller_reviews >= SUSPICIOUS_SELLER_REVIEW_THRESHOLD:
            return ReviewModerationStatus.pending, "repeat_buyer_seller_pattern"
        recent_purchases_same_seller = await self._repo.count_recent_completed_purchases_between_users(
            buyer_user_id=author_user_id,
            seller_user_id=seller_user_id,
            hours=24,
        )
        if recent_purchases_same_seller >= SUSPICIOUS_SELLER_REVIEW_THRESHOLD:
            return ReviewModerationStatus.pending, "dense_buyer_seller_activity"
        if normalized_text and await self._repo.has_duplicate_review_text(
            author_user_id=author_user_id,
            seller_user_id=seller_user_id,
            text=normalized_text,
            exclude_review_id=existing_review.id if existing_review is not None else None,
        ):
            return ReviewModerationStatus.pending, "duplicate_review_text"
        return ReviewModerationStatus.visible, None

    async def upsert_review(
        self,
        *,
        user: User,
        prompt_id: uuid.UUID,
        payload: PromptReviewWrite,
    ) -> PromptReviewRead:
        purchase = await self._repo.get_reviewable_purchase(user_id=user.id, prompt_id=prompt_id)
        if (
            purchase is None
            or purchase.status != PurchaseStatus.completed
            or purchase.settlement_status in {MarketplaceSettlementStatus.refunded, MarketplaceSettlementStatus.disputed}
        ):
            raise AppError(code="review_not_allowed", message="Only verified purchasers can leave a review.", status_code=403)
        if purchase.seller_user_id == user.id:
            raise AppError(code="review_not_allowed", message="You can't review your own prompt.", status_code=403)
        if purchase.prompt is None:
            prompt = await self._repo.get_prompt_by_id(prompt_id)
            if prompt is None:
                raise NotFoundError("prompt", str(prompt_id))
            purchase.prompt = prompt
        prompt = purchase.prompt
        review = purchase.review or await self._repo.get_review_by_purchase_id(purchase.id)
        normalized_text = payload.text.strip() if payload.text else None
        moderation_status, moderation_reason = await self._review_moderation_state(
            author_user_id=user.id,
            seller_user_id=purchase.seller_user_id,
            review_text=normalized_text,
            existing_review=review,
        )
        if review is None:
            try:
                review = await self._repo.create_review(
                    prompt_purchase_id=purchase.id,
                    prompt_id=prompt.id,
                    seller_user_id=purchase.seller_user_id,
                    author_user_id=user.id,
                    rating=payload.rating,
                    body=normalized_text,
                )
            except IntegrityError:
                review = await self._repo.get_review_by_purchase_id(purchase.id)
                if review is None:
                    raise
                review.rating = payload.rating
                review.body = normalized_text
        else:
            review.rating = payload.rating
            review.body = normalized_text
            review.edit_count += 1
        review.moderation_status = moderation_status
        review.moderation_reason = moderation_reason
        review.is_visible = moderation_status == ReviewModerationStatus.visible
        review.hidden_at = None if review.is_visible else datetime.now(timezone.utc)
        await self._repo.save_review(review)
        author_slug = await self._repo.get_contributor_slug_for_user(user.id)
        return self._review_to_read(review, prompt, user, author_slug)

    async def seller_summary(
        self,
        *,
        seller_user_id: uuid.UUID,
        reputation_tier: str | None = None,
        review_sort: ReviewSort = ReviewSort.new,
        review_limit: int = 6,
    ) -> SellerMarketplaceSummaryRead:
        await self.refresh_settlement_states(seller_user_id=seller_user_id)
        summary = await self._repo.get_seller_summary(seller_user_id)
        reviews = await self._repo.list_reviews_for_seller(seller_user_id=seller_user_id, sort=review_sort, limit=review_limit)
        payouts = await self._repo.list_recent_payouts(seller_user_id, limit=4)
        recent_reviews = [
            self._review_to_read(review, prompt, author, author_profile.slug if author_profile is not None else None)
            for review, prompt, author, author_profile in reviews
        ]
        rating_average = summary["rating_average"]
        return SellerMarketplaceSummaryRead(
            rating_average=rating_average,
            rating_display=round_rating(rating_average if isinstance(rating_average, float) else None),
            review_count=int(summary["review_count"] or 0),
            sold_prompts_count=int(summary["sold_prompts_count"] or 0),
            purchases_count=int(summary["purchases_count"] or 0),
            seller_revenue_rub=int(summary["seller_revenue_rub"] or 0),
            seller_lumens_earned=int(summary["seller_lumens_earned"] or 0),
            pending_balance_rub=int(summary["pending_balance_rub"] or 0),
            available_balance_rub=int(summary["available_balance_rub"] or 0),
            paid_out_rub=int(summary["paid_out_rub"] or 0),
            refunded_balance_rub=int(summary["refunded_balance_rub"] or 0),
            disputed_balance_rub=int(summary["disputed_balance_rub"] or 0),
            pending_balance_lumens=int(summary["pending_balance_lumens"] or 0),
            available_balance_lumens=int(summary["available_balance_lumens"] or 0),
            paid_out_lumens=int(summary["paid_out_lumens"] or 0),
            refunded_balance_lumens=int(summary["refunded_balance_lumens"] or 0),
            disputed_balance_lumens=int(summary["disputed_balance_lumens"] or 0),
            platform_commission_rub=int(summary["platform_commission_rub"] or 0),
            platform_commission_lumens=int(summary["platform_commission_lumens"] or 0),
            clawback_due_rub=int(summary["clawback_due_rub"] or 0),
            clawback_due_lumens=int(summary["clawback_due_lumens"] or 0),
            payout_eligible=(
                int(summary["available_balance_rub"] or 0) > 0
                or int(summary["available_balance_lumens"] or 0) > 0
            ),
            trust_indicators=self._trust_indicators(
                review_count=int(summary["review_count"] or 0),
                rating_average=rating_average if isinstance(rating_average, float) else None,
                sold_prompts_count=int(summary["sold_prompts_count"] or 0),
                reputation_tier=reputation_tier,
            ),
            recent_reviews=recent_reviews,
            recent_payouts=[self._payout_to_read(row) for row in payouts],
        )

    async def list_seller_reviews(
        self,
        *,
        seller_user_id: uuid.UUID,
        sort: ReviewSort,
        limit: int = 20,
    ) -> PromptReviewListRead:
        rating_average, review_count = await self._repo.get_seller_rating_snapshot(seller_user_id)
        rows = await self._repo.list_reviews_for_seller(seller_user_id=seller_user_id, sort=sort, limit=limit)
        items = [
            self._review_to_read(review, prompt, author, author_profile.slug if author_profile is not None else None)
            for review, prompt, author, author_profile in rows
        ]
        return PromptReviewListRead(
            seller_user_id=seller_user_id,
            rating_average=rating_average,
            rating_display=round_rating(rating_average),
            review_count=review_count,
            sort=sort,
            items=items,
        )

    async def overview_for_user(self, user: User, *, reputation_tier: str | None = None) -> MarketplaceOverviewRead:
        summary = await self.seller_summary(
            seller_user_id=user.id,
            reputation_tier=reputation_tier,
            review_sort=ReviewSort.new,
            review_limit=4,
        )
        purchases = await self._repo.list_recent_user_purchases(user.id, limit=8)
        reviews = await self.list_seller_reviews(seller_user_id=user.id, sort=ReviewSort.new, limit=4)
        payouts = await self._repo.list_recent_payouts(user.id, limit=4)
        return MarketplaceOverviewRead(
            summary=summary,
            purchases=[self._purchase_to_read(row, can_review=row.status == PurchaseStatus.completed) for row in purchases],
            reviews=reviews.items,
            payouts=[self._payout_to_read(row) for row in payouts],
        )
