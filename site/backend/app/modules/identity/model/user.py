import uuid
from datetime import datetime

from pydantic import BaseModel

from app.infrastructure.db.models import PlanTier, UserRole


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: UserRole
    plan_tier: PlanTier
    created_at: datetime

    model_config = {"from_attributes": True}
