from __future__ import annotations

import uuid

from sqlalchemy import inspect as sa_inspect

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import (
    MarketplacePayout,
    Prompt,
    PromptPrice,
    PromptPurchase,
    PromptReview,
    PurchaseStatus,
    User,
)
from app.modules.marketplace.model.marketplace import (
    MarketplaceOverviewRead,
    MarketplacePayoutRead,
    PromptPurchaseRead,
    PromptReviewListRead,
    PromptReviewRead,
    ReviewSort,
    SellerMarketplaceSummaryRead,
    TrustIndicatorRead,
)
from app.modules.marketplace.service.policy import (
    MARKETPLACE_COMMISSION_PERCENT,
    normalize_prompt_price,
    round_rating,
)


class MarketplaceProjectionMixin:
    def _payout_to_read(self, payout: MarketplacePayout) -> MarketplacePayoutRead:
        return self._payouts.payout_to_read(payout)

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
        return await self._reviews.list_seller_reviews(
            seller_user_id=seller_user_id,
            sort=sort,
            limit=limit,
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
