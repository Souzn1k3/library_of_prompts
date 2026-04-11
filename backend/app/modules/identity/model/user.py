import uuid
from datetime import datetime

from pydantic import BaseModel

from app.infrastructure.db.models import PlanTier, UserRole
from app.modules.marketplace.model.marketplace import TrustIndicatorRead


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None
    telegram_language: str | None = None
    role: UserRole
    plan_tier: PlanTier
    mission_credits: int = 0
    premium_unlock_until: datetime | None = None
    contributor_slug: str | None = None
    rating_average: float | None = None
    rating_display: float | None = None
    review_count: int = 0
    sold_prompts_count: int = 0
    purchases_count: int = 0
    seller_revenue_rub: int = 0
    seller_lumens_earned: int = 0
    trust_indicators: list[TrustIndicatorRead] = []
    created_at: datetime

    model_config = {"from_attributes": True}
