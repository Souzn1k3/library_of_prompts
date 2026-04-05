from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.orm import aliased, selectinload

from app.infrastructure.db.models import (
    ContributorProfile,
    MarketplaceSettlementStatus,
    Prompt,
    PromptPrice,
    PromptPurchase,
    PromptReview,
    PromptReviewReport,
    PurchaseStatus,
    ReviewModerationStatus,
    User,
)
from app.modules.marketplace.model.marketplace import ReviewSort


class MarketplaceReviewMixin:
    async def get_review_by_purchase_id(self, purchase_id: uuid.UUID) -> PromptReview | None:
        stmt = select(PromptReview).where(PromptReview.prompt_purchase_id == purchase_id).limit(1)
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
        return [
            (review, prompt, author, author_profile if author_profile is not None else None)
            for review, prompt, author, author_profile in result.all()
        ]

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
