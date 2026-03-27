import uuid
from datetime import datetime

from pydantic import BaseModel

from app.infrastructure.db.models import ContributorTier


class ContributorStats(BaseModel):
    total_submissions: int
    approved_submissions: int
    rejected_submissions: int
    rejection_rate: int
    total_saves: int
    total_copies: int
    mission_success_count: int
    average_prompt_quality: int


class ContributorProfileRead(BaseModel):
    user_id: uuid.UUID
    slug: str
    display_name: str
    bio: str | None = None
    reputation_score: int
    reputation_tier: ContributorTier
    stats: ContributorStats
    computed_at: datetime | None = None


class ContributorTopItem(BaseModel):
    user_id: uuid.UUID
    slug: str
    display_name: str
    reputation_score: int
    reputation_tier: ContributorTier
    approved_submissions: int
    total_saves: int
