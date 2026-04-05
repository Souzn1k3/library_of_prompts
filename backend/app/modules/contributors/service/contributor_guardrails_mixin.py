from __future__ import annotations

from app.core.errors import AppError
from app.infrastructure.db.models import ContributorTier, User


class ContributorGuardrailsMixin:
    async def apply_submission_guardrails(self, user: User, *, title: str, body: str) -> None:
        profile = await self.ensure_profile(user)
        if profile.reputation_tier == ContributorTier.top:
            daily_limit = 20
            pending_limit = 8
        elif profile.reputation_tier == ContributorTier.verified:
            daily_limit = 10
            pending_limit = 4
        else:
            daily_limit = 5
            pending_limit = 2

        recent_count = await self._repo.count_recent_submissions(user.id, hours=24)
        if recent_count >= daily_limit:
            raise AppError(
                code="submission_rate_limited",
                message="You've reached the submission limit for the last 24 hours.",
                status_code=429,
                details={"daily_limit": daily_limit},
            )

        pending_count = await self._repo.count_pending_submissions(user.id)
        if pending_count >= pending_limit:
            raise AppError(
                code="submission_pending_limit",
                message="You already have too many prompts waiting for review. Please wait for feedback first.",
                status_code=409,
                details={"pending_limit": pending_limit},
            )

        has_duplicate = await self._repo.has_recent_duplicate_submission(
            user.id,
            title=title,
            body=body,
            hours=24,
        )
        if has_duplicate:
            raise AppError(
                code="duplicate_submission",
                message="A very similar submission was already sent in the last 24 hours.",
                status_code=409,
            )

        if profile.reputation_tier == ContributorTier.new and len(body.strip()) < 120:
            raise AppError(
                code="submission_too_short",
                message="Please add more detail before submitting.",
                status_code=400,
                details={"minimum_body_chars": 120},
            )

    async def should_auto_approve(self, user: User) -> bool:
        profile = await self.ensure_profile(user)
        if profile.reputation_tier != ContributorTier.top:
            return False
        if profile.approved_submissions < 20:
            return False
        if profile.rejection_rate > 8:
            return False
        return True

    def feedback_hints(self, notes: str | None) -> list[str]:
        if not notes:
            return []
        text = notes.lower()
        hints: list[str] = []
        if "unclear" in text or "not clear" in text:
            hints.append("Clarify the objective and expected output format.")
        if "too short" in text or "lack" in text:
            hints.append("Add more context, constraints, and an explicit example.")
        if "duplicate" in text:
            hints.append("Differentiate this prompt with a unique use-case or structure.")
        if "unsafe" in text or "policy" in text:
            hints.append("Avoid unsafe instructions and align with policy-safe use.")
        if not hints:
            hints.append("Review moderation notes and tighten structure before resubmitting.")
        return hints
