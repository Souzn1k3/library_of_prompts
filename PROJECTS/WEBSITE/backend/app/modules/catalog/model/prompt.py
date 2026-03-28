import enum
import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import (
    ContributorTier,
    ModerationState,
    PromptDifficulty,
    PromptOutputType,
    PromptStatus,
    PromptTechnique,
    StoreItemKind,
)


class PromptSort(str, enum.Enum):
    relevance = "relevance"
    trending = "trending"
    most_used = "most_used"
    newest = "newest"
    most_saved = "most_saved"


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
    difficulty: PromptDifficulty | None = None
    output_type: PromptOutputType | None = None
    use_cases: list[str] = []
    model_compatibility: list[str] = []
    tags: list[str] = []
    save_count: int = 0
    copy_count: int = 0
    quality_score: int = 0
    contributor_slug: str | None = None
    contributor_tier: ContributorTier | None = None
    contributor_reputation_score: int | None = None
    recommendation_reason_key: str | None = None

    model_config = {"from_attributes": True}


class StoreUnlockOffer(BaseModel):
    item_slug: str
    item_title: str
    price: int
    currency: str = "LMN"
    kind: StoreItemKind


class PromptRead(PromptListItem):
    body: str = Field(min_length=1)
    body_locked: bool = False
    unlock_offer: StoreUnlockOffer | None = None


class PromptDiscoveryFilters(BaseModel):
    use_cases: list[dict[str, str]]
    model_compatibility: list[dict[str, str]]
    tags: list[dict[str, str]]
    difficulties: list[str]
    output_types: list[str]
    sorts: list[str]


class DiscoverySections(BaseModel):
    for_you: list[PromptListItem] = []
    trending: list[PromptListItem]
    best_for_beginners: list[PromptListItem]
    most_saved: list[PromptListItem]


_SUBMIT_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PromptSubmit(BaseModel):
    slug: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    category_id: uuid.UUID
    technique: PromptTechnique = PromptTechnique.other
    difficulty: PromptDifficulty | None = None
    output_type: PromptOutputType | None = None
    use_cases: list[str] = Field(default_factory=list, max_length=8)
    tags: list[str] = Field(default_factory=list, max_length=12)
    model_compatibility: list[str] = Field(default_factory=list, max_length=8)

    model_config = {"extra": "forbid"}

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        s = v.strip().lower()
        if not _SUBMIT_SLUG.match(s):
            raise ValueError("Use only lowercase letters, numbers, and hyphens.")
        return s

    @field_validator("use_cases", "tags", "model_compatibility", mode="before")
    @classmethod
    def normalize_list_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            raw = [part.strip() for part in value.split(",")]
        elif isinstance(value, list):
            raw = [str(part).strip() for part in value]
        else:
            raise ValueError("Please provide a list of values.")
        return [item.lower() for item in raw if item]


class AuthorPromptRow(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    status: PromptStatus
    moderation_state: ModerationState
    moderation_notes: str | None = None
    moderated_at: datetime | None = None
    auto_approved: bool = False
    feedback_hints: list[str] = []
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
    contributor_tier: ContributorTier | None = None
    contributor_reputation_score: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptSubmissionResult(BaseModel):
    id: uuid.UUID
    slug: str
    status: PromptStatus
    moderation_state: ModerationState
    auto_approved: bool = False


class ModerationDecision(BaseModel):
    action: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)
