import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.infrastructure.db.models import PlanTier


class LessonListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    min_tier: PlanTier
    sort_order: int
    created_at: datetime
    locked: bool = False

    model_config = {"from_attributes": True}


class LessonRead(LessonListItem):
    body: str = Field(min_length=1)
    body_locked: bool = False


class PopularLessonItem(LessonListItem):
    completion_count: int = 0
