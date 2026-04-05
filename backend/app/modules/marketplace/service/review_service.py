from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.infrastructure.db.models import (
    MarketplaceSettlementStatus,
    Prompt,
    PromptReview,
    PurchaseStatus,
    ReviewModerationStatus,
    User,
)
from app.modules.marketplace.model.marketplace import (
    PromptReviewListRead,
    PromptReviewRead,
    PromptReviewReportWrite,
    PromptReviewWrite,
    ReviewSort,
)
from app.modules.marketplace.repository.marketplace_repository import MarketplaceRepository
from app.modules.marketplace.service.policy import (
    MAX_AUTHOR_REVIEWS_PER_24H,
    MAX_REVIEW_EDITS,
    REVIEW_EDIT_COOLDOWN_MINUTES,
    REVIEW_HIDE_REPORT_THRESHOLD,
    SUSPICIOUS_SELLER_REVIEW_THRESHOLD,
    round_rating,
)


class MarketplaceReviewService:
    def __init__(
        self,
        repo: MarketplaceRepository,
        review_to_read: Callable[[PromptReview, Prompt, User, str | None], PromptReviewRead],
    ) -> None:
        self._repo = repo
        self._review_to_read = review_to_read

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
