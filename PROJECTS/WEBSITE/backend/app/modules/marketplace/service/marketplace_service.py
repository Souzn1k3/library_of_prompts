from __future__ import annotations

import math
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.tiers import is_staff
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
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

try:
    import stripe
except Exception:  # pragma: no cover - runtime optional
    stripe = None


_MARKETPLACE_COMMISSION_PERCENT = 5
_LUMEN_PRICE_MULTIPLIER = 4
_MIN_PROMPT_PRICE_RUB = 49
_MAX_PROMPT_PRICE_RUB = 4999
_SETTLEMENT_HOLD_DAYS = 7
_REVIEW_EDIT_COOLDOWN_MINUTES = 15
_MAX_REVIEW_EDITS = 6
_REVIEW_HIDE_REPORT_THRESHOLD = 3
_MAX_AUTHOR_REVIEWS_PER_24H = 8
_SUSPICIOUS_SELLER_REVIEW_THRESHOLD = 3
_ALLOWED_PAYOUT_CURRENCIES = frozenset({"RUB", "LMN"})


@dataclass(slots=True)
class PlanAccessContext:
    total_unlocks: int = 0
    remaining_unlocks: int = 0
    money_discount_percent: int = 0
    lumen_discount_percent: int = 0


def price_lumens_from_rub(price_rub: int) -> int:
    return max(120, int(price_rub) * _LUMEN_PRICE_MULTIPLIER)


def normalize_prompt_price(price_rub: int | None) -> tuple[int, int] | None:
    if price_rub is None or price_rub <= 0:
        return None
    if price_rub < _MIN_PROMPT_PRICE_RUB or price_rub > _MAX_PROMPT_PRICE_RUB:
        raise AppError(
            code="invalid_prompt_price",
            message=f"Prompt price must be between {_MIN_PROMPT_PRICE_RUB} and {_MAX_PROMPT_PRICE_RUB} RUB.",
            status_code=400,
            details={
                "minimum_price_rub": _MIN_PROMPT_PRICE_RUB,
                "maximum_price_rub": _MAX_PROMPT_PRICE_RUB,
            },
        )
    return int(price_rub), price_lumens_from_rub(int(price_rub))


def _round_rating(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value) + 1e-8, 1)


def _fee(amount: int) -> int:
    if amount <= 0:
        return 0
    return max(1, int(math.ceil(amount * (_MARKETPLACE_COMMISSION_PERCENT / 100.0))))


def _apply_discount(amount: int, discount_percent: int) -> int:
    if amount <= 0 or discount_percent <= 0:
        return amount
    return max(1, int(round(amount * (100 - discount_percent) / 100.0)))


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _start_of_current_month(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    return start, end


def _settlement_available_at(completed_at: datetime | None) -> datetime | None:
    if completed_at is None:
        return None
    return completed_at + timedelta(days=_SETTLEMENT_HOLD_DAYS)


def _append_query(url: str, **params: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({k: v for k, v in params.items() if v})
    encoded = urlencode(query)
    return urlunparse(parsed._replace(query=encoded))


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

    def _seller_amount_for_currency(self, purchase: PromptPurchase, currency_code: str) -> int:
        if currency_code.upper() == "LMN":
            return int(purchase.seller_amount_lumens or 0)
        return int(purchase.seller_amount_rub or 0)

    def _payout_to_read(self, payout: MarketplacePayout) -> MarketplacePayoutRead:
        return MarketplacePayoutRead(
            id=payout.id,
            currency_code=payout.currency_code,
            status=payout.status,
            total_amount=payout.total_amount,
            purchase_count=payout.purchase_count,
            external_reference=payout.external_reference,
            requested_at=payout.requested_at,
            paid_at=payout.paid_at,
        )

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
        return MarketplaceSettlementStatus.pending, _settlement_available_at(completed_at)

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
        normalized = currency_code.strip().upper()
        if normalized not in _ALLOWED_PAYOUT_CURRENCIES:
            raise AppError(
                code="invalid_payout_currency",
                message="Unsupported payout currency.",
                status_code=400,
                details={"allowed": sorted(_ALLOWED_PAYOUT_CURRENCIES)},
            )
        return normalized

    def _client_token_scope(self, user_id: uuid.UUID, client_token: str, *, prefix: str) -> str:
        digest = sha256(client_token.encode("utf-8")).hexdigest()[:32]
        return f"{prefix}:{user_id.hex}:{digest}"[:80]

    def _scoped_client_token(self, user_id: uuid.UUID, client_token: str | None, *, prefix: str) -> str:
        raw = (client_token or "").strip()
        if raw:
            return self._client_token_scope(user_id, raw, prefix=prefix)
        return f"{prefix}:{user_id.hex}:{secrets.token_hex(8)}"[:80]

    def _candidate_client_tokens(self, user_id: uuid.UUID, client_token: str, *, prefix: str) -> list[str]:
        raw = client_token.strip()
        if not raw:
            return []
        scoped = self._client_token_scope(user_id, raw, prefix=prefix)
        if scoped == raw:
            return [scoped]
        return [scoped, raw]

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
        return [
            purchase
            for purchase in payout.purchases
            if purchase.status == PurchaseStatus.completed
            and purchase.settlement_status == MarketplaceSettlementStatus.available
            and purchase.payout_id == payout.id
        ]

    async def _sync_reserved_payout(self, payout: MarketplacePayout) -> MarketplacePayout:
        payout_state = sa_inspect(payout)
        if "purchases" in payout_state.unloaded:
            loaded_payout = await self._repo.get_payout_by_id(payout.id, for_update=True)
            if loaded_payout is None:
                raise NotFoundError("marketplace_payout", str(payout.id))
            payout = loaded_payout
        eligible = self._eligible_payout_purchases(payout)
        payout.purchase_count = len(eligible)
        payout.total_amount = sum(
            self._seller_amount_for_currency(purchase, payout.currency_code)
            for purchase in eligible
        )
        if payout.status in {MarketplacePayoutStatus.requested, MarketplacePayoutStatus.processing} and payout.purchase_count == 0:
            payout.status = MarketplacePayoutStatus.canceled
        payout = await self._repo.save_payout(payout)
        loaded_payout = await self._repo.get_payout_by_id(payout.id, for_update=True)
        if loaded_payout is None:
            raise NotFoundError("marketplace_payout", str(payout.id))
        return loaded_payout

    async def _release_payout_reservations(self, payout: MarketplacePayout) -> None:
        for purchase in payout.purchases:
            if purchase.payout_id != payout.id:
                continue
            if purchase.settlement_status == MarketplaceSettlementStatus.paid_out:
                continue
            purchase.payout_id = None
            await self._repo.save_purchase(purchase)

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
        now = now or datetime.now(timezone.utc)
        released = 0
        rows = await self._repo.list_settlement_ready_purchases(
            seller_user_id=seller_user_id,
            now=now,
            for_update=True,
        )
        for purchase in rows:
            purchase.settlement_status = MarketplaceSettlementStatus.available
            await self._repo.save_purchase(purchase)
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_available,
                currency_code="LMN" if purchase.seller_amount_lumens > 0 else "RUB",
                amount=max(purchase.seller_amount_lumens, purchase.seller_amount_rub),
                meta={"purchase_id": str(purchase.id)},
            )
            released += 1
        return released

    async def create_payout_batch(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        notes: str | None = None,
    ) -> MarketplacePayoutRead:
        normalized_currency = self._normalize_payout_currency(currency_code)
        await self.refresh_settlement_states(seller_user_id=seller_user_id)
        purchases = await self._repo.list_available_purchases_for_payout(
            seller_user_id=seller_user_id,
            currency_code=normalized_currency,
            for_update=True,
        )
        if not purchases:
            raise AppError(
                code="no_payout_balance",
                message="There are no available earnings ready for payout.",
                status_code=409,
            )
        total_amount = sum(self._seller_amount_for_currency(purchase, normalized_currency) for purchase in purchases)
        payout = await self._repo.create_payout(
            seller_user_id=seller_user_id,
            currency_code=normalized_currency,
            total_amount=total_amount,
            purchase_count=len(purchases),
            notes=notes,
        )
        for purchase in purchases:
            purchase.payout_id = payout.id
            await self._repo.save_purchase(purchase)
        payout = await self._sync_reserved_payout(payout)
        return self._payout_to_read(payout)

    async def mark_payout_processing(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            return self._payout_to_read(payout)
        if payout.status in {MarketplacePayoutStatus.failed, MarketplacePayoutStatus.canceled}:
            raise AppError(
                code="payout_not_processable",
                message="This payout can no longer be processed.",
                status_code=409,
            )
        payout = await self._sync_reserved_payout(payout)
        if payout.purchase_count <= 0:
            raise AppError(
                code="payout_empty",
                message="This payout no longer has eligible earnings attached.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.processing
        await self._repo.save_payout(payout)
        return self._payout_to_read(payout)

    async def fail_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be failed.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.failed
        await self._release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self._payout_to_read(payout)

    async def cancel_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be canceled.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.canceled
        await self._release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self._payout_to_read(payout)

    async def finalize_payout(
        self,
        *,
        payout_id: uuid.UUID,
        reference: str | None = None,
        now: datetime | None = None,
    ) -> MarketplacePayoutRead:
        now = now or datetime.now(timezone.utc)
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            return self._payout_to_read(payout)
        if payout.status in {MarketplacePayoutStatus.failed, MarketplacePayoutStatus.canceled}:
            raise AppError(
                code="payout_not_payable",
                message="This payout is no longer payable.",
                status_code=409,
            )
        payout = await self._sync_reserved_payout(payout)
        eligible_purchases = self._eligible_payout_purchases(payout)
        if not eligible_purchases:
            raise AppError(
                code="payout_empty",
                message="This payout no longer has eligible earnings attached.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.paid
        payout.external_reference = reference
        payout.paid_at = now
        payout.purchase_count = len(eligible_purchases)
        payout.total_amount = sum(
            self._seller_amount_for_currency(purchase, payout.currency_code)
            for purchase in eligible_purchases
        )
        for purchase in eligible_purchases:
            purchase.settlement_status = MarketplaceSettlementStatus.paid_out
            purchase.paid_out_at = now
            await self._repo.save_purchase(purchase)
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=purchase.prompt_id,
                actor_user_id=purchase.seller_user_id,
                kind=MarketplaceTransactionKind.seller_payout,
                currency_code=payout.currency_code,
                amount=self._seller_amount_for_currency(purchase, payout.currency_code),
                meta={"purchase_id": str(purchase.id), "payout_id": str(payout.id)},
            )
        await self._repo.save_payout(payout)
        if payout.currency_code.upper() == "LMN" and payout.seller_user_id is not None and payout.total_amount > 0:
            await self._wallet.adjust_balance(
                user_id=payout.seller_user_id,
                amount=payout.total_amount,
                reason=CurrencyTransactionType.marketplace_sale,
                context=f"marketplace:payout:{payout.id}",
                source_id=payout.id,
                metadata={"payout_id": str(payout.id), "currency_code": payout.currency_code},
                now=now,
            )
        return self._payout_to_read(payout)

    async def _resolve_usage_window(self, user: User) -> tuple[datetime, datetime]:
        latest = await self._billing.get_latest_subscription_for_user(user.id)
        if (
            latest is not None
            and latest.plan is not None
            and latest.plan.tier == user.plan_tier
            and latest.status in {SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due}
        ):
            start = _ensure_aware(latest.current_period_start)
            end = _ensure_aware(latest.current_period_end)
            if start is not None and end is not None and end > start:
                return start, end
        return _start_of_current_month(datetime.now(timezone.utc))

    async def _get_or_create_plan_usage_window(
        self,
        *,
        user: User,
        window_started_at: datetime,
        window_ends_at: datetime,
        for_update: bool,
    ):
        usage = await self._repo.get_plan_usage_window(
            user_id=user.id,
            plan_tier=user.plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        if usage is not None:
            return usage

        plan = await self._billing.get_plan_by_tier(user.plan_tier)
        included_limit = int(plan.monthly_paid_prompt_limit) if plan is not None else 0
        try:
            return await self._repo.create_plan_usage_window(
                user_id=user.id,
                plan_tier=user.plan_tier,
                window_started_at=window_started_at,
                window_ends_at=window_ends_at,
                included_paid_prompt_limit=included_limit,
            )
        except IntegrityError:
            await self._repo.rollback()
            usage = await self._repo.get_plan_usage_window(
                user_id=user.id,
                plan_tier=user.plan_tier,
                window_started_at=window_started_at,
                window_ends_at=window_ends_at,
                for_update=for_update,
            )
            if usage is None:
                raise
            return usage

    async def get_plan_access_context(self, user: User, *, for_update: bool = False) -> PlanAccessContext:
        plan = await self._billing.get_plan_by_tier(user.plan_tier)
        if plan is None:
            return PlanAccessContext()
        window_started_at, window_ends_at = await self._resolve_usage_window(user)
        usage = await self._get_or_create_plan_usage_window(
            user=user,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            for_update=for_update,
        )
        total = int(plan.monthly_paid_prompt_limit or 0)
        used = int(usage.used_paid_prompt_unlocks or 0)
        return PlanAccessContext(
            total_unlocks=total,
            remaining_unlocks=max(total - used, 0),
            money_discount_percent=int(plan.prompt_purchase_discount_percent or 0),
            lumen_discount_percent=int(plan.lumen_purchase_discount_percent or 0),
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
        if prompt.author_id == viewer.id:
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.author.value)
        if is_staff(viewer):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.staff.value)
        entitlement = await self._repo.get_entitlement(
            user_id=viewer.id,
            prompt_id=prompt.id,
            for_update=auto_grant_included_unlock,
        )
        if entitlement is not None:
            return PromptAccessRead(has_access=True, is_owned=True, source=entitlement.source.value)
        if await self._store.user_has_prompt_access(user_id=viewer.id, prompt_id=prompt.id):
            return PromptAccessRead(has_access=True, is_owned=True, source=PromptAccessSource.legacy_store.value)
        plan_context = await self.get_plan_access_context(viewer, for_update=auto_grant_included_unlock)
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
        await self._grant_included_unlock(prompt=prompt, user=viewer, plan_context=plan_context)
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
        prompt: Prompt,
        user: User,
        plan_context: PlanAccessContext,
    ) -> PromptPurchase:
        if plan_context.remaining_unlocks <= 0:
            raise AppError(
                code="plan_unlocks_exhausted",
                message="You've used all included paid prompt unlocks for the current period.",
                status_code=402,
            )
        window_started_at, window_ends_at = await self._resolve_usage_window(user)
        usage = await self._get_or_create_plan_usage_window(
            user=user,
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
        plan_token = f"plan-{user.id}-{prompt.id}"
        now = datetime.now(timezone.utc)
        try:
            purchase = await self._repo.create_purchase(
                user_id=user.id,
                prompt_id=prompt.id,
                seller_user_id=prompt.author_id,
                payment_method=PromptPaymentMethod.included_limit,
                status=PurchaseStatus.completed,
                settlement_status=MarketplaceSettlementStatus.available,
                price_rub=0,
                price_lumens=0,
                client_token=plan_token,
                settlement_available_at=now,
                completed_at=now,
                meta={"included_unlock": True, "plan_tier": user.plan_tier.value},
            )
        except IntegrityError:
            await self._repo.rollback()
            existing = await self._repo.get_purchase_by_client_token(user_id=user.id, client_token=plan_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                return existing
            raise

        entitlement = await self._repo.try_create_entitlement(
            user_id=user.id,
            prompt_id=prompt.id,
            source=PromptAccessSource.subscription_limit,
            purchase_id=purchase.id,
            meta={"plan_tier": user.plan_tier.value},
            granted_at=now,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(user_id=user.id, prompt_id=prompt.id, for_update=True)
            if entitlement is None:
                raise

        usage.used_paid_prompt_unlocks += 1
        await self._repo.save_plan_usage_window(usage)
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt.id,
            actor_user_id=user.id,
            kind=MarketplaceTransactionKind.included_unlock,
            currency_code="PLAN",
            amount=1,
            meta={"plan_tier": user.plan_tier.value},
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
                commission_percent=_MARKETPLACE_COMMISSION_PERCENT,
                is_active=True,
            )
            prompt.pricing = pricing
        else:
            pricing.price_rub = price_rub_value
            pricing.price_lumens = price_lumens_value
            pricing.commission_percent = _MARKETPLACE_COMMISSION_PERCENT
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
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        if prompt.author_id == user.id:
            raise AppError(code="cannot_buy_own_prompt", message="You can't buy your own prompt.", status_code=400)

        if payload.client_token:
            existing = await self._find_purchase_by_client_token(
                user_id=user.id,
                client_token=payload.client_token,
                prefix=token_prefix,
            )
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = await self.resolve_prompt_access(prompt, user, auto_grant_included_unlock=False)
                return PromptPurchaseActionResponse(purchase=self._purchase_to_read(existing), access=access)

        active_purchase = await self._repo.get_active_purchase(user_id=user.id, prompt_id=prompt.id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")
        current_access = await self.resolve_prompt_access(prompt, user, auto_grant_included_unlock=False)
        if current_access.is_owned:
            raise ConflictError("You already own this prompt.")

        effective_client_token = self._scoped_client_token(user.id, payload.client_token, prefix=token_prefix)
        plan_context = await self.get_plan_access_context(user)
        effective_price_lumens = _apply_discount(prompt.pricing.price_lumens, plan_context.lumen_discount_percent)
        fee_lumens = _fee(effective_price_lumens)
        seller_lumens = max(effective_price_lumens - fee_lumens, 0)
        now = datetime.now(timezone.utc)
        settlement_status, settlement_available_at = self._initial_settlement_status(
            seller_amount_rub=0,
            seller_amount_lumens=seller_lumens,
            completed_at=now,
        )
        try:
            purchase = await self._repo.create_purchase(
                user_id=user.id,
                prompt_id=prompt.id,
                seller_user_id=prompt.author_id,
                payment_method=PromptPaymentMethod.lumens,
                status=PurchaseStatus.pending,
                settlement_status=settlement_status,
                price_rub=0,
                price_lumens=effective_price_lumens,
                platform_fee_lumens=fee_lumens,
                seller_amount_lumens=seller_lumens,
                settlement_available_at=settlement_available_at,
                client_token=effective_client_token,
                meta={"base_price_lumens": prompt.pricing.price_lumens},
            )
        except IntegrityError as exc:
            await self._repo.rollback()
            existing = await self._repo.get_purchase_by_client_token(user_id=user.id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                access = await self.resolve_prompt_access(prompt, user, auto_grant_included_unlock=False)
                return PromptPurchaseActionResponse(purchase=self._purchase_to_read(existing), access=access)
            raise ConflictError("A purchase for this prompt is already being processed.") from exc
        purchase.prompt = prompt
        await self._wallet.adjust_balance(
            user_id=user.id,
            amount=-effective_price_lumens,
            reason=CurrencyTransactionType.marketplace_purchase,
            context=f"prompt:{prompt.id}:purchase:{purchase.id}:buyer",
            source_id=purchase.id,
            metadata={"prompt_id": str(prompt.id), "purchase_id": str(purchase.id)},
            now=now,
        )
        purchase.status = PurchaseStatus.completed
        purchase.completed_at = now
        await self._repo.save_purchase(purchase)
        entitlement = await self._repo.try_create_entitlement(
            user_id=user.id,
            prompt_id=prompt.id,
            source=PromptAccessSource.direct_lumens,
            purchase_id=purchase.id,
            meta={"payment_method": PromptPaymentMethod.lumens.value},
            granted_at=now,
        )
        if entitlement is None:
            entitlement = await self._repo.get_entitlement(user_id=user.id, prompt_id=prompt.id, for_update=True)
            if entitlement is None:
                raise
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt.id,
            actor_user_id=user.id,
            kind=MarketplaceTransactionKind.buyer_charge,
            currency_code="LMN",
            amount=effective_price_lumens,
            meta={"prompt_id": str(prompt.id)},
        )
        if prompt.author_id is not None and seller_lumens > 0:
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt.id,
                actor_user_id=prompt.author_id,
                kind=MarketplaceTransactionKind.seller_credit,
                currency_code="LMN",
                amount=seller_lumens,
                meta={"prompt_id": str(prompt.id)},
            )
        await self._repo.create_marketplace_transaction(
            prompt_purchase_id=purchase.id,
            prompt_id=prompt.id,
            actor_user_id=None,
            kind=MarketplaceTransactionKind.platform_fee,
            currency_code="LMN",
            amount=fee_lumens,
            meta={"prompt_id": str(prompt.id)},
        )
        access = await self.resolve_prompt_access(prompt, user, auto_grant_included_unlock=False)
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
        prompt = await self._repo.get_prompt_by_id(payload.prompt_id)
        if prompt is None:
            raise NotFoundError("prompt", str(payload.prompt_id))
        if prompt.pricing is None or not prompt.pricing.is_active:
            raise AppError(code="prompt_not_paid", message="This prompt does not require a paid unlock.", status_code=400)
        if prompt.author_id == user.id:
            raise AppError(code="cannot_buy_own_prompt", message="You can't buy your own prompt.", status_code=400)
        existing_access = await self.resolve_prompt_access(prompt, user, auto_grant_included_unlock=False)
        if existing_access.is_owned:
            raise ConflictError("You already own this prompt.")
        if payload.client_token:
            existing = await self._find_purchase_by_client_token(
                user_id=user.id,
                client_token=payload.client_token,
                prefix=token_prefix,
            )
            if existing is not None and existing.status == PurchaseStatus.completed:
                raise ConflictError("This prompt is already purchased.")
        active_purchase = await self._repo.get_active_purchase(user_id=user.id, prompt_id=prompt.id)
        if active_purchase is not None:
            raise ConflictError("A purchase for this prompt is already being processed.")
        effective_client_token = self._scoped_client_token(user.id, payload.client_token, prefix=token_prefix)
        plan_context = await self.get_plan_access_context(user)
        effective_price_rub = _apply_discount(prompt.pricing.price_rub, plan_context.money_discount_percent)
        fee_rub = _fee(effective_price_rub)
        seller_rub = max(effective_price_rub - fee_rub, 0)
        try:
            purchase = await self._repo.create_purchase(
                user_id=user.id,
                prompt_id=prompt.id,
                seller_user_id=prompt.author_id,
                payment_method=PromptPaymentMethod.stripe,
                status=PurchaseStatus.pending,
                price_rub=effective_price_rub,
                price_lumens=0,
                platform_fee_rub=fee_rub,
                seller_amount_rub=seller_rub,
                client_token=effective_client_token,
                meta={"base_price_rub": prompt.pricing.price_rub},
            )
        except IntegrityError as exc:
            await self._repo.rollback()
            existing = await self._repo.get_purchase_by_client_token(user_id=user.id, client_token=effective_client_token)
            if existing is not None and existing.status == PurchaseStatus.completed:
                raise ConflictError("This prompt is already purchased.") from exc
            raise ConflictError("A purchase for this prompt is already being processed.") from exc
        success_url = self._resolve_checkout_redirect_url(
            payload.success_url,
            default_url=_append_query(self._settings.billing_checkout_success_url, prompt=prompt.slug),
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
                user_id=user.id,
                prompt_id=prompt.id,
                source=PromptAccessSource.direct_money,
                purchase_id=purchase.id,
                meta={"payment_method": PromptPaymentMethod.stripe.value, "mock": True},
                granted_at=completed_at,
            )
            if entitlement is None:
                entitlement = await self._repo.get_entitlement(user_id=user.id, prompt_id=prompt.id, for_update=True)
                if entitlement is None:
                    raise
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt.id,
                actor_user_id=user.id,
                kind=MarketplaceTransactionKind.buyer_charge,
                currency_code="RUB",
                amount=effective_price_rub,
                meta={"prompt_id": str(prompt.id), "mock": True},
            )
            await self._repo.create_marketplace_transaction(
                prompt_purchase_id=purchase.id,
                prompt_id=prompt.id,
                actor_user_id=None,
                kind=MarketplaceTransactionKind.platform_fee,
                currency_code="RUB",
                amount=fee_rub,
                meta={"prompt_id": str(prompt.id), "mock": True},
            )
            if prompt.author_id is not None and seller_rub > 0:
                await self._repo.create_marketplace_transaction(
                    prompt_purchase_id=purchase.id,
                    prompt_id=prompt.id,
                    actor_user_id=prompt.author_id,
                    kind=MarketplaceTransactionKind.seller_credit,
                    currency_code="RUB",
                    amount=seller_rub,
                    meta={"prompt_id": str(prompt.id), "mock": True},
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
                            "name": prompt.title,
                            "description": prompt.summary or "Paid prompt unlock",
                        },
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(user.id),
            metadata={
                "kind": "prompt_purchase",
                "purchase_id": str(purchase.id),
                "prompt_id": str(prompt.id),
                "user_id": str(user.id),
            },
            payment_intent_data={
                "metadata": {
                    "kind": "prompt_purchase",
                    "purchase_id": str(purchase.id),
                    "prompt_id": str(prompt.id),
                    "user_id": str(user.id),
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
        if review.reported_count >= _REVIEW_HIDE_REPORT_THRESHOLD:
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
        if existing_review is not None and existing_review.edit_count >= _MAX_REVIEW_EDITS:
            raise AppError(
                code="review_edit_limit_reached",
                message="This review has reached the edit limit.",
                status_code=409,
            )
        if existing_review is not None and existing_review.updated_at is not None:
            cooldown_until = existing_review.updated_at + timedelta(minutes=_REVIEW_EDIT_COOLDOWN_MINUTES)
            if datetime.now(timezone.utc) < cooldown_until:
                raise AppError(
                    code="review_edit_cooldown",
                    message="Please wait a bit before editing this review again.",
                    status_code=429,
                )
        recent_reviews = await self._repo.count_recent_reviews_by_author(author_user_id=author_user_id, hours=24)
        if recent_reviews >= _MAX_AUTHOR_REVIEWS_PER_24H:
            return ReviewModerationStatus.pending, "review_velocity"
        same_seller_reviews = await self._repo.count_reviews_for_seller_by_author(
            seller_user_id=seller_user_id,
            author_user_id=author_user_id,
        )
        if same_seller_reviews >= _SUSPICIOUS_SELLER_REVIEW_THRESHOLD:
            return ReviewModerationStatus.pending, "repeat_buyer_seller_pattern"
        recent_purchases_same_seller = await self._repo.count_recent_completed_purchases_between_users(
            buyer_user_id=author_user_id,
            seller_user_id=seller_user_id,
            hours=24,
        )
        if recent_purchases_same_seller >= _SUSPICIOUS_SELLER_REVIEW_THRESHOLD:
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
            rating_display=_round_rating(rating_average if isinstance(rating_average, float) else None),
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
            rating_display=_round_rating(rating_average),
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
