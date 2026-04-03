from pydantic import BaseModel

from app.infrastructure.db.models import PlanTier


class AdminTierUpdate(BaseModel):
    plan_tier: PlanTier
