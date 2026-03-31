import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, and_, desc, distinct, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.infrastructure.db.models import (
    ContributorProfile,
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransaction,
    MarketplaceTransactionKind,
    PlanTier,
    PlanUsageWindow,
    Prompt,
    PromptAccessSource,
    PromptEntitlement,
    PromptPrice,
    PromptPurchase,
    PromptReview,
    PromptReviewReport,
    PurchaseStatus,
    ReviewModerationStatus,
    User,
)
from app.modules.marketplace.model.marketplace import ReviewSort


class MarketplaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def rollback(self) -> None:
        await self._session.rollback()

    def _supports_for_update(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name != "sqlite")

    def _maybe_for_update(self, stmt: Select, enabled: bool) -> Select:
        if enabled and self._supports_for_update():
            return stmt.with_for_update()
        return stmt

    async def get_prompt_price(self, prompt_id: uuid.UUID) -> PromptPrice | None:
        result = await self._session.execute(select(PromptPrice).where(PromptPrice.prompt_id == prompt_id))
        return result.scalar_one_or_none()

    async def list_prompt_prices(self, prompt_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, PromptPrice]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return {}
        result = await self._session.execute(select(PromptPrice).where(PromptPrice.prompt_id.in_(ids)))
        return {row.prompt_id: row for row in result.scalars().all()}

    async def get_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        for_update: bool = False,
    ) -> PromptEntitlement | None:
        stmt = (
            select(PromptEntitlement)
            .options(selectinload(PromptEntitlement.purchase))
            .where(
                PromptEntitlement.user_id == user_id,
                PromptEntitlement.prompt_id == prompt_id,
                PromptEntitlement.revoked_at.is_(None),
            )
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_entitled_prompt_ids(
        self,
        *,
        user_id: uuid.UUID,
        prompt_ids: Sequence[uuid.UUID],
    ) -> set[uuid.UUID]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return set()
        result = await self._session.execute(
            select(PromptEntitlement.prompt_id).where(
                PromptEntitlement.user_id == user_id,
                PromptEntitlement.prompt_id.in_(ids),
                PromptEntitlement.revoked_at.is_(None),
            )
        )
        return {row[0] for row in result.all()}

    async def create_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        source: PromptAccessSource,
        purchase_id: uuid.UUID | None = None,
        meta: dict | None = None,
        granted_at: datetime | None = None,
    ) -> PromptEntitlement:
        entitlement = PromptEntitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=source,
            purchase_id=purchase_id,
            meta=meta,
            granted_at=granted_at or datetime.now(timezone.utc),
        )
        self._session.add(entitlement)
        await self._session.flush()
        await self._session.refresh(entitlement)
        return entitlement

    async def try_create_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        source: PromptAccessSource,
        purchase_id: uuid.UUID | None = None,
        meta: dict | None = None,
        granted_at: datetime | None = None,
    ) -> PromptEntitlement | None:
        entitlement = PromptEntitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=source,
            purchase_id=purchase_id,
            meta=meta,
            granted_at=granted_at or datetime.now(timezone.utc),
        )
        try:
            async with self._session.begin_nested():
                self._session.add(entitlement)
                await self._session.flush()
        except IntegrityError:
            return None
        await self._session.refresh(entitlement)
        return entitlement

    async def save_entitlement(self, entitlement: PromptEntitlement) -> PromptEntitlement:
        await self._session.flush()
        await self._session.refresh(entitlement)
        return entitlement

    async def get_purchase_by_client_token(
        self,
        *,
        user_id: uuid.UUID,
        client_token: str,
    ) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.client_token == client_token,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_id(self, purchase_id: uuid.UUID, *, for_update: bool = False) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(PromptPurchase.id == purchase_id)
            .limit(1)
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_provider_checkout_id(self, checkout_id: str) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(PromptPurchase.provider_checkout_id == checkout_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_provider_payment_id(self, payment_id: str) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(PromptPurchase.provider_payment_id == payment_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_completed_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.completed,
            )
            .order_by(PromptPurchase.completed_at.desc().nullslast(), PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.pending,
            )
            .order_by(PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        payment_method,
        status: PurchaseStatus,
        settlement_status: MarketplaceSettlementStatus = MarketplaceSettlementStatus.pending,
        price_rub: int,
        price_lumens: int,
        platform_fee_rub: int = 0,
        seller_amount_rub: int = 0,
        platform_fee_lumens: int = 0,
        seller_amount_lumens: int = 0,
        settlement_available_at: datetime | None = None,
        paid_out_at: datetime | None = None,
        disputed_at: datetime | None = None,
        payout_id: uuid.UUID | None = None,
        provider_checkout_id: str | None = None,
        provider_payment_id: str | None = None,
        client_token: str | None = None,
        completed_at: datetime | None = None,
        refunded_at: datetime | None = None,
        meta: dict | None = None,
    ) -> PromptPurchase:
        purchase = PromptPurchase(
            user_id=user_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            payment_method=payment_method,
            status=status,
            settlement_status=settlement_status,
            price_rub=price_rub,
            price_lumens=price_lumens,
            platform_fee_rub=platform_fee_rub,
            seller_amount_rub=seller_amount_rub,
            platform_fee_lumens=platform_fee_lumens,
            seller_amount_lumens=seller_amount_lumens,
            settlement_available_at=settlement_available_at,
            paid_out_at=paid_out_at,
            disputed_at=disputed_at,
            payout_id=payout_id,
            provider_checkout_id=provider_checkout_id,
            provider_payment_id=provider_payment_id,
            client_token=client_token,
            completed_at=completed_at,
            refunded_at=refunded_at,
            meta=meta,
        )
        self._session.add(purchase)
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase

    async def save_purchase(self, purchase: PromptPurchase) -> PromptPurchase:
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase

    async def list_settlement_ready_purchases(
        self,
        *,
        seller_user_id: uuid.UUID | None,
        now: datetime,
        limit: int = 200,
        for_update: bool = False,
    ) -> list[PromptPurchase]:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.status == PurchaseStatus.completed,
                PromptPurchase.settlement_status == MarketplaceSettlementStatus.pending,
                PromptPurchase.settlement_available_at.is_not(None),
                PromptPurchase.settlement_available_at <= now,
            )
            .order_by(PromptPurchase.settlement_available_at.asc(), PromptPurchase.created_at.asc())
            .limit(limit)
        )
        if seller_user_id is not None:
            stmt = stmt.where(PromptPurchase.seller_user_id == seller_user_id)
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_available_purchases_for_payout(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        limit: int = 200,
        for_update: bool = False,
    ) -> list[PromptPurchase]:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.seller_user_id == seller_user_id,
                PromptPurchase.status == PurchaseStatus.completed,
                PromptPurchase.settlement_status == MarketplaceSettlementStatus.available,
                PromptPurchase.payout_id.is_(None),
            )
            .order_by(PromptPurchase.completed_at.asc().nullslast(), PromptPurchase.created_at.asc())
            .limit(limit)
        )
        if currency_code.upper() == "LMN":
            stmt = stmt.where(PromptPurchase.seller_amount_lumens > 0)
        else:
            stmt = stmt.where(PromptPurchase.seller_amount_rub > 0)
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_payout(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        total_amount: int,
        purchase_count: int,
        notes: str | None = None,
    ) -> MarketplacePayout:
        payout = MarketplacePayout(
            seller_user_id=seller_user_id,
            currency_code=currency_code,
            status=MarketplacePayoutStatus.requested,
            total_amount=total_amount,
            purchase_count=purchase_count,
            notes=notes,
        )
        self._session.add(payout)
        await self._session.flush()
        await self._session.refresh(payout)
        return payout

    async def get_payout_by_id(self, payout_id: uuid.UUID, *, for_update: bool = False) -> MarketplacePayout | None:
        stmt = (
            select(MarketplacePayout)
            .options(selectinload(MarketplacePayout.purchases))
            .where(MarketplacePayout.id == payout_id)
            .limit(1)
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_payout(self, payout: MarketplacePayout) -> MarketplacePayout:
        await self._session.flush()
        await self._session.refresh(payout)
        return payout

    async def list_recent_payouts(self, seller_user_id: uuid.UUID, *, limit: int = 6) -> list[MarketplacePayout]:
        stmt = (
            select(MarketplacePayout)
            .where(MarketplacePayout.seller_user_id == seller_user_id)
            .order_by(MarketplacePayout.requested_at.desc(), MarketplacePayout.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        for_update: bool = False,
    ) -> PlanUsageWindow | None:
        stmt = select(PlanUsageWindow).where(
            PlanUsageWindow.user_id == user_id,
            PlanUsageWindow.plan_tier == plan_tier,
            PlanUsageWindow.window_started_at == window_started_at,
            PlanUsageWindow.window_ends_at == window_ends_at,
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_plan_usage_window(
        self,
        *,
        user_id: uuid.UUID,
        plan_tier: PlanTier,
        window_started_at: datetime,
        window_ends_at: datetime,
        included_paid_prompt_limit: int,
        used_paid_prompt_unlocks: int = 0,
    ) -> PlanUsageWindow:
        row = PlanUsageWindow(
            user_id=user_id,
            plan_tier=plan_tier,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            included_paid_prompt_limit=included_paid_prompt_limit,
            used_paid_prompt_unlocks=used_paid_prompt_unlocks,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_plan_usage_window(self, row: PlanUsageWindow) -> PlanUsageWindow:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def create_marketplace_transaction(
        self,
        *,
        prompt_purchase_id: uuid.UUID | None,
        prompt_id: uuid.UUID | None,
        actor_user_id: uuid.UUID | None,
        kind: MarketplaceTransactionKind,
        currency_code: str,
        amount: int,
        meta: dict | None = None,
    ) -> MarketplaceTransaction:
        row = MarketplaceTransaction(
            prompt_purchase_id=prompt_purchase_id,
            prompt_id=prompt_id,
            actor_user_id=actor_user_id,
            kind=kind,
            currency_code=currency_code,
            amount=amount,
            meta=meta,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_review_by_purchase_id(self, purchase_id: uuid.UUID) -> PromptReview | None:
        stmt = (
            select(PromptReview)
            .where(PromptReview.prompt_purchase_id == purchase_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_review(
        self,
        *,
        prompt_purchase_id: uuid.UUID,
        prompt_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        author_user_id: uuid.UUID,
        rating: int,
        body: str | None,
    ) -> PromptReview:
        row = PromptReview(
            prompt_purchase_id=prompt_purchase_id,
            prompt_id=prompt_id,
            seller_user_id=seller_user_id,
            author_user_id=author_user_id,
            rating=rating,
            body=body,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_review(self, review: PromptReview) -> PromptReview:
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def get_review_by_id(self, review_id: uuid.UUID) -> PromptReview | None:
        stmt = (
            select(PromptReview)
            .options(
                selectinload(PromptReview.prompt),
                selectinload(PromptReview.author).selectinload(User.contributor_profile),
            )
            .where(PromptReview.id == review_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_recent_reviews_by_author(self, *, author_user_id: uuid.UUID, hours: int) -> int:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(func.count(PromptReview.id)).where(
            PromptReview.author_user_id == author_user_id,
            PromptReview.created_at >= since,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def count_reviews_for_seller_by_author(
        self,
        *,
        seller_user_id: uuid.UUID | None,
        author_user_id: uuid.UUID,
    ) -> int:
        if seller_user_id is None:
            return 0
        stmt = select(func.count(PromptReview.id)).where(
            PromptReview.seller_user_id == seller_user_id,
            PromptReview.author_user_id == author_user_id,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def count_recent_completed_purchases_between_users(
        self,
        *,
        buyer_user_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        hours: int,
    ) -> int:
        if seller_user_id is None:
            return 0
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(func.count(PromptPurchase.id)).where(
            PromptPurchase.user_id == buyer_user_id,
            PromptPurchase.seller_user_id == seller_user_id,
            PromptPurchase.status == PurchaseStatus.completed,
            PromptPurchase.completed_at.is_not(None),
            PromptPurchase.completed_at >= since,
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def has_duplicate_review_text(
        self,
        *,
        author_user_id: uuid.UUID,
        seller_user_id: uuid.UUID | None,
        text: str,
        exclude_review_id: uuid.UUID | None = None,
    ) -> bool:
        if seller_user_id is None or not text.strip():
            return False
        stmt = select(PromptReview.id).where(
            PromptReview.author_user_id == author_user_id,
            PromptReview.seller_user_id == seller_user_id,
            func.lower(func.trim(PromptReview.body)) == text.strip().lower(),
        )
        if exclude_review_id is not None:
            stmt = stmt.where(PromptReview.id != exclude_review_id)
        stmt = stmt.limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_review_report(
        self,
        *,
        review_id: uuid.UUID,
        reporter_user_id: uuid.UUID,
        reason: str,
        details: str | None,
    ) -> PromptReviewReport:
        row = PromptReviewReport(
            review_id=review_id,
            reporter_user_id=reporter_user_id,
            reason=reason,
            details=details,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def count_review_reports(self, review_id: uuid.UUID) -> int:
        stmt = select(func.count(PromptReviewReport.id)).where(PromptReviewReport.review_id == review_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_recent_user_purchases(self, user_id: uuid.UUID, *, limit: int = 12) -> list[PromptPurchase]:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(PromptPurchase.user_id == user_id)
            .order_by(PromptPurchase.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_reviewable_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .options(
                selectinload(PromptPurchase.prompt),
                selectinload(PromptPurchase.review),
                selectinload(PromptPurchase.review)
                .selectinload(PromptReview.author)
                .selectinload(User.contributor_profile),
            )
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.completed,
            )
            .order_by(PromptPurchase.completed_at.desc().nullslast(), PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_reviews_for_seller(
        self,
        *,
        seller_user_id: uuid.UUID,
        sort: ReviewSort,
        limit: int = 20,
    ) -> list[tuple[PromptReview, Prompt, User, ContributorProfile | None]]:
        author_profile = aliased(ContributorProfile)
        stmt = (
            select(PromptReview, Prompt, User, author_profile)
            .join(Prompt, Prompt.id == PromptReview.prompt_id)
            .join(User, User.id == PromptReview.author_user_id)
            .outerjoin(author_profile, author_profile.user_id == User.id)
            .where(
                PromptReview.seller_user_id == seller_user_id,
                PromptReview.is_visible.is_(True),
                PromptReview.moderation_status == ReviewModerationStatus.visible,
            )
        )
        if sort == ReviewSort.best:
            stmt = stmt.order_by(desc(PromptReview.rating), desc(PromptReview.created_at))
        else:
            stmt = stmt.order_by(desc(PromptReview.created_at))
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.all())

    async def get_seller_summary(self, seller_user_id: uuid.UUID) -> dict[str, int | float | None]:
        purchase_stmt = (
            select(
                PromptPurchase.settlement_status,
                func.count(PromptPurchase.id),
                func.coalesce(func.sum(PromptPurchase.seller_amount_rub), 0),
                func.coalesce(func.sum(PromptPurchase.seller_amount_lumens), 0),
                func.coalesce(func.sum(PromptPurchase.platform_fee_rub), 0),
                func.coalesce(func.sum(PromptPurchase.platform_fee_lumens), 0),
            )
            .where(
                PromptPurchase.seller_user_id == seller_user_id,
                PromptPurchase.status.in_([PurchaseStatus.completed, PurchaseStatus.refunded]),
            )
            .group_by(PromptPurchase.settlement_status)
        )
        purchase_rows = (await self._session.execute(purchase_stmt)).all()
        settlement_totals: dict[str, dict[str, int]] = {}
        completed_count = 0
        seller_revenue_rub = 0
        seller_lumens_earned = 0
        commission_rub = 0
        commission_lumens = 0
        for status, count, seller_rub, seller_lumens, fee_rub, fee_lumens in purchase_rows:
            key = status.value if isinstance(status, MarketplaceSettlementStatus) else str(status)
            settlement_totals[key] = {
                "count": int(count or 0),
                "seller_rub": int(seller_rub or 0),
                "seller_lumens": int(seller_lumens or 0),
            }
            if key != MarketplaceSettlementStatus.refunded.value:
                completed_count += int(count or 0)
                seller_revenue_rub += int(seller_rub or 0)
                seller_lumens_earned += int(seller_lumens or 0)
                commission_rub += int(fee_rub or 0)
                commission_lumens += int(fee_lumens or 0)

        sold_prompt_stmt = (
            select(func.count(distinct(Prompt.id)))
            .join(PromptPrice, PromptPrice.prompt_id == Prompt.id)
            .where(
                Prompt.author_id == seller_user_id,
                PromptPrice.is_active.is_(True),
            )
        )
        sold_prompts_count = int((await self._session.execute(sold_prompt_stmt)).scalar_one() or 0)

        rating_stmt = (
            select(
                func.count(PromptReview.id),
                func.avg(PromptReview.rating),
            )
            .where(
                PromptReview.seller_user_id == seller_user_id,
                PromptReview.is_visible.is_(True),
                PromptReview.moderation_status == ReviewModerationStatus.visible,
            )
        )
        rating_row = (await self._session.execute(rating_stmt)).one()

        clawback_stmt = (
            select(
                func.coalesce(func.sum(PromptPurchase.seller_amount_rub), 0),
                func.coalesce(func.sum(PromptPurchase.seller_amount_lumens), 0),
            )
            .where(
                PromptPurchase.seller_user_id == seller_user_id,
                PromptPurchase.status == PurchaseStatus.refunded,
                PromptPurchase.paid_out_at.is_not(None),
            )
        )
        clawback_row = (await self._session.execute(clawback_stmt)).one()

        return {
            "purchases_count": completed_count,
            "seller_revenue_rub": seller_revenue_rub,
            "seller_lumens_earned": seller_lumens_earned,
            "sold_prompts_count": sold_prompts_count,
            "review_count": int(rating_row[0] or 0),
            "rating_average": float(rating_row[1]) if rating_row[1] is not None else None,
            "pending_balance_rub": settlement_totals.get(MarketplaceSettlementStatus.pending.value, {}).get("seller_rub", 0),
            "available_balance_rub": settlement_totals.get(MarketplaceSettlementStatus.available.value, {}).get("seller_rub", 0),
            "paid_out_rub": settlement_totals.get(MarketplaceSettlementStatus.paid_out.value, {}).get("seller_rub", 0),
            "refunded_balance_rub": settlement_totals.get(MarketplaceSettlementStatus.refunded.value, {}).get("seller_rub", 0),
            "disputed_balance_rub": settlement_totals.get(MarketplaceSettlementStatus.disputed.value, {}).get("seller_rub", 0),
            "pending_balance_lumens": settlement_totals.get(MarketplaceSettlementStatus.pending.value, {}).get("seller_lumens", 0),
            "available_balance_lumens": settlement_totals.get(MarketplaceSettlementStatus.available.value, {}).get("seller_lumens", 0),
            "paid_out_lumens": settlement_totals.get(MarketplaceSettlementStatus.paid_out.value, {}).get("seller_lumens", 0),
            "refunded_balance_lumens": settlement_totals.get(MarketplaceSettlementStatus.refunded.value, {}).get("seller_lumens", 0),
            "disputed_balance_lumens": settlement_totals.get(MarketplaceSettlementStatus.disputed.value, {}).get("seller_lumens", 0),
            "platform_commission_rub": commission_rub,
            "platform_commission_lumens": commission_lumens,
            "clawback_due_rub": int(clawback_row[0] or 0),
            "clawback_due_lumens": int(clawback_row[1] or 0),
        }

    async def get_seller_rating_snapshot(self, seller_user_id: uuid.UUID) -> tuple[float | None, int]:
        stmt = (
            select(func.avg(PromptReview.rating), func.count(PromptReview.id))
            .where(
                PromptReview.seller_user_id == seller_user_id,
                PromptReview.is_visible.is_(True),
                PromptReview.moderation_status == ReviewModerationStatus.visible,
            )
        )
        row = (await self._session.execute(stmt)).one()
        return (float(row[0]) if row[0] is not None else None, int(row[1] or 0))

    async def get_contributor_slug_for_user(self, user_id: uuid.UUID) -> str | None:
        stmt = select(ContributorProfile.slug).where(ContributorProfile.user_id == user_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_prompt_by_id(self, prompt_id: uuid.UUID) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                selectinload(Prompt.pricing),
                selectinload(Prompt.author).selectinload(User.contributor_profile),
            )
            .where(Prompt.id == prompt_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_prompt_by_slug(self, slug: str) -> Prompt | None:
        stmt = (
            select(Prompt)
            .options(
                selectinload(Prompt.pricing),
                selectinload(Prompt.author).selectinload(User.contributor_profile),
            )
            .where(Prompt.slug == slug)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
