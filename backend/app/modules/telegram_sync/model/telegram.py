import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import PlanTier


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def normalize_language_code(value: str | None) -> str:
    raw = (value or "ru").strip().lower()
    if raw in {"en", "eng"}:
        return "eng"
    if raw in {"tt", "tat"}:
        return "tat"
    if raw == "ru":
        return "ru"
    return (raw or "ru")[:10]


class TelegramUserUpsert(BaseModel):
    telegram_user_id: int = Field(gt=0)
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    language: str = Field(default="ru", min_length=2, max_length=10)
    is_active: bool = True

    @field_validator("username", "first_name", "last_name", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return _normalize_optional(value)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return normalize_language_code(value)


class TelegramProfileRead(BaseModel):
    user_id: uuid.UUID
    telegram_user_id: int
    display_name: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language: str = "ru"
    plan_tier: PlanTier
    is_premium: bool = False
    is_active: bool = True
    joined_at: datetime
    last_active: datetime | None = None
    prompts_submitted: int = 0
    prompts_saved: int = 0
    days_in_bot: int = 1


class TelegramActiveUserRead(BaseModel):
    telegram_user_id: int
    language: str = "ru"
    first_name: str | None = None


class TelegramPromptRead(BaseModel):
    id: uuid.UUID
    legacy_bot_prompt_id: int | None = None
    slug: str
    title: str
    body: str
    body_locked: bool = False
    is_premium: bool = False
    legacy_bot_category: str | None = None
    legacy_bot_subcategory: str | None = None
    content_language: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TelegramRewardClaimWrite(BaseModel):
    claim_id: str = Field(min_length=8, max_length=120)
    telegram_user_id: int = Field(gt=0)
    reward_tokens: int = Field(ge=1, le=1000)
    reason: str = Field(min_length=1, max_length=200)
    challenge_key: str | None = Field(default=None, max_length=120)
    occurred_at: datetime
    signature: str = Field(min_length=1, max_length=128)

    @field_validator("claim_id", "reason", "challenge_key", mode="before")
    @classmethod
    def normalize_claim_strings(cls, value: str | None) -> str | None:
        return _normalize_optional(value)


class TelegramRewardClaimRead(BaseModel):
    claim_id: str
    telegram_user_id: int
    reward_tokens: int
    verified: bool
    applied: bool
    verification_error: str | None = None
    applied_at: datetime | None = None
    balance_after: int | None = None
