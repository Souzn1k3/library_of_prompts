from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.errors import NotFoundError
from app.infrastructure.db.models import ContributorProfile, ContributorTier, User
from app.modules.contributors.model.contributor import ContributorProfileRead, ContributorTopItem
from app.modules.contributors.service.contributor_support import clamp, slugify, to_profile_read
from app.modules.marketplace.model.marketplace import ReviewSort


class ContributorProfileMixin:
    async def ensure_profile(self, user: User) -> ContributorProfile:
        existing = await self._repo.get_profile_by_user_id(user.id)
        if existing is not None:
            return existing

        base = slugify(user.display_name)
        slug = base
        suffix = 1
        while await self._repo.slug_exists(slug):
            suffix += 1
            slug = f"{base}-{suffix}"

        profile = ContributorProfile(user_id=user.id, slug=slug)
        return await self._repo.create_profile(profile)

    def _score(self, snapshot: dict[str, int]) -> tuple[int, ContributorTier]:
        total = max(snapshot["total_submissions"], 1)
        approved = snapshot["approved_submissions"]
        rejected = snapshot["rejected_submissions"]
        reviewed = max(approved + rejected, 1)

        approval_rate = approved / reviewed
        rejection_ratio = rejected / reviewed
        avg_saves = snapshot["total_saves"] / max(approved, 1)
        avg_copies = snapshot["total_copies"] / max(approved, 1)
        mission_success = snapshot["mission_success_count"] / max(approved, 1)
        avg_quality = snapshot["average_prompt_quality"] / 100.0

        approval_component = approval_rate * 45.0
        save_component = clamp(avg_saves / 6.0, 0.0, 1.0) * 20.0
        usage_component = clamp(avg_copies / 12.0, 0.0, 1.0) * 20.0
        mission_component = clamp(mission_success / 4.0, 0.0, 1.0) * 10.0
        quality_component = clamp(avg_quality, 0.0, 1.0) * 5.0
        rejection_penalty = rejection_ratio * 15.0
        volume_penalty = 0.0 if total <= 5 else clamp((total - approved) / total, 0.0, 1.0) * 5.0

        score = int(round(clamp(
            approval_component
            + save_component
            + usage_component
            + mission_component
            + quality_component
            - rejection_penalty
            - volume_penalty,
            0.0,
            100.0,
        )))

        if score >= 78 and approved >= 20 and approval_rate >= 0.88 and avg_saves >= 2.5:
            tier = ContributorTier.top
        elif score >= 45 and approved >= 5 and approval_rate >= 0.65:
            tier = ContributorTier.verified
        else:
            tier = ContributorTier.new

        return score, tier

    async def recompute_profile_for_user_id(self, user_id: uuid.UUID) -> ContributorProfile:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("user", str(user_id))

        profile = await self.ensure_profile(user)
        snapshot = await self._repo.calculate_user_signal_snapshot(user.id)
        score, tier = self._score(snapshot)

        profile.reputation_score = score
        profile.reputation_tier = tier
        profile.total_submissions = snapshot["total_submissions"]
        profile.approved_submissions = snapshot["approved_submissions"]
        profile.rejected_submissions = snapshot["rejected_submissions"]
        profile.rejection_rate = snapshot["rejection_rate"]
        profile.total_saves = snapshot["total_saves"]
        profile.total_copies = snapshot["total_copies"]
        profile.mission_success_count = snapshot["mission_success_count"]
        profile.average_prompt_quality = snapshot["average_prompt_quality"]
        profile.computed_at = datetime.now(timezone.utc)
        return await self._repo.save_profile(profile)

    async def recompute_profile_for_user(self, user: User) -> ContributorProfile:
        await self.ensure_profile(user)
        return await self.recompute_profile_for_user_id(user.id)

    async def refresh_prompt_quality(self, prompt_id: uuid.UUID) -> None:
        quality = await self._repo.calculate_prompt_quality_snapshot(prompt_id)
        if quality is None:
            return
        await self._repo.upsert_prompt_quality_metric(prompt_id, quality)
        author_id = await self._repo.get_prompt_author_id(prompt_id)
        if author_id is not None:
            await self.recompute_profile_for_user_id(author_id)

    async def get_public_profile(
        self,
        slug: str,
        *,
        review_sort: ReviewSort = ReviewSort.new,
        review_limit: int = 6,
    ) -> ContributorProfileRead:
        profile = await self._repo.get_profile_by_slug(slug)
        if profile is None:
            raise NotFoundError("contributor", slug)
        base = to_profile_read(profile)
        if self._marketplace is None:
            return base
        summary = await self._marketplace.seller_summary(
            seller_user_id=profile.user_id,
            reputation_tier=profile.reputation_tier.value,
            review_sort=review_sort,
            review_limit=review_limit,
        )
        return ContributorProfileRead(**base.model_dump(), **summary.model_dump())

    async def list_top(self, *, limit: int = 12) -> list[ContributorTopItem]:
        rows = await self._repo.list_top_profiles(limit=limit)
        out: list[ContributorTopItem] = []
        for row in rows:
            if row.user is None:
                continue
            out.append(
                ContributorTopItem(
                    user_id=row.user_id,
                    slug=row.slug,
                    display_name=row.user.display_name,
                    reputation_score=row.reputation_score,
                    reputation_tier=row.reputation_tier,
                    approved_submissions=row.approved_submissions,
                    total_saves=row.total_saves,
                )
            )
        return out
