import uuid
from datetime import datetime

from pydantic import BaseModel

from app.infrastructure.db.models import ContributorTier
from app.modules.marketplace.model.marketplace import PromptReviewRead, TrustIndicatorRead


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
    rating_average: float | None = None
    rating_display: float | None = None
    review_count: int = 0
    sold_prompts_count: int = 0
    purchases_count: int = 0
    seller_revenue_rub: int = 0
    seller_lumens_earned: int = 0
    trust_indicators: list[TrustIndicatorRead] = []
    recent_reviews: list[PromptReviewRead] = []
    computed_at: datetime | None = None


class ContributorTopItem(BaseModel):
    user_id: uuid.UUID
    slug: str
    display_name: str
    reputation_score: int
    reputation_tier: ContributorTier
    approved_submissions: int
    total_saves: int
