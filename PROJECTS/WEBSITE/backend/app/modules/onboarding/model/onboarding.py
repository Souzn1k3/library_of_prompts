import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.infrastructure.db.models import OnboardingGoal, OnboardingRole, PlanTier


class OnboardingProfileRead(BaseModel):
    role: OnboardingRole | None = None
    goal: OnboardingGoal | None = None
    ai_context: str | None = None
    completed_at: datetime | None = None
    skipped_at: datetime | None = None
    first_win_prompt_id: uuid.UUID | None = None
    first_win_completed_at: datetime | None = None
    is_completed: bool
    is_skipped: bool
    needs_onboarding: bool

    model_config = {"from_attributes": True}


class OnboardingProfileUpdate(BaseModel):
    role: OnboardingRole
    goal: OnboardingGoal
    ai_context: str = Field(min_length=1, max_length=120)

    model_config = {"extra": "forbid"}


class OnboardingStarterPrompt(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None
    technique: str
    category_id: uuid.UUID


class OnboardingStarterLesson(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    min_tier: PlanTier
    locked: bool


class OnboardingStarterAction(BaseModel):
    prompt_id: uuid.UUID
    prompt_slug: str
    prompt_title: str
    prompt_body: str
    instruction: str


class OnboardingStarterPack(BaseModel):
    prompts: list[OnboardingStarterPrompt]
    lesson: OnboardingStarterLesson | None
    action: OnboardingStarterAction | None


class FirstWinCompleteRequest(BaseModel):
    prompt_id: uuid.UUID
    action: str = Field(min_length=1, max_length=64)

    model_config = {"extra": "forbid"}
