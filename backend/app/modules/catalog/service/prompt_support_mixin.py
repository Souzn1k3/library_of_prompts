from __future__ import annotations

from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import Prompt, User
from app.modules.catalog.model.prompt import PromptRead


class PromptServiceSupportMixin:
    def _restrict_catalog(self, viewer: User | None) -> bool:
        return not can_view_restricted_category(viewer)

    @staticmethod
    def _contributor_tier_value(row: Prompt) -> str | None:
        if row.author is None or row.author.contributor_profile is None:
            return None
        return row.author.contributor_profile.reputation_tier.value

    async def _attach_author_rating(self, read: PromptRead, row: Prompt) -> None:
        if self._marketplace is None or row.author_id is None:
            return
        summary = await self._marketplace.seller_summary(
            seller_user_id=row.author_id,
            reputation_tier=self._contributor_tier_value(row),
            review_limit=3,
        )
        read.author_rating_average = summary.rating_average
        read.author_rating_count = summary.review_count
