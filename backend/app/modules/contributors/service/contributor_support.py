from __future__ import annotations

import re

from app.infrastructure.db.models import ContributorProfile
from app.modules.contributors.model.contributor import ContributorProfileRead, ContributorStats


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "contributor"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_profile_read(profile: ContributorProfile) -> ContributorProfileRead:
    if profile.user is None:
        display_name = "Contributor"
    else:
        display_name = profile.user.display_name
    return ContributorProfileRead(
        user_id=profile.user_id,
        slug=profile.slug,
        display_name=display_name,
        bio=profile.bio,
        reputation_score=profile.reputation_score,
        reputation_tier=profile.reputation_tier,
        stats=ContributorStats(
            total_submissions=profile.total_submissions,
            approved_submissions=profile.approved_submissions,
            rejected_submissions=profile.rejected_submissions,
            rejection_rate=profile.rejection_rate,
            total_saves=profile.total_saves,
            total_copies=profile.total_copies,
            mission_success_count=profile.mission_success_count,
            average_prompt_quality=profile.average_prompt_quality,
        ),
        computed_at=profile.computed_at,
    )
