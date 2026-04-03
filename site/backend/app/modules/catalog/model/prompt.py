import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import ModerationState, PromptStatus, PromptTechnique


class PromptListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    status: PromptStatus
    technique: PromptTechnique
    moderation_state: ModerationState
    category_id: uuid.UUID
    author_id: uuid.UUID | None
    created_at: datetime
    is_premium: bool = False

    model_config = {"from_attributes": True}


class PromptRead(PromptListItem):
    body: str = Field(min_length=1)
    body_locked: bool = False


_SUBMIT_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PromptSubmit(BaseModel):
    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    category_id: uuid.UUID
    technique: PromptTechnique = PromptTechnique.other

    model_config = {"extra": "forbid"}

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        s = v.strip().lower()
        if not _SUBMIT_SLUG.match(s):
            raise ValueError("slug must be lowercase kebab-case")
        return s


class AuthorPromptRow(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    status: PromptStatus
    moderation_state: ModerationState
    created_at: datetime

    model_config = {"from_attributes": True}


class ModerationQueueItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    category_id: uuid.UUID
    author_id: uuid.UUID | None
    technique: PromptTechnique
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptSubmissionResult(BaseModel):
    id: uuid.UUID
    slug: str
    status: PromptStatus
    moderation_state: ModerationState


class ModerationDecision(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)
