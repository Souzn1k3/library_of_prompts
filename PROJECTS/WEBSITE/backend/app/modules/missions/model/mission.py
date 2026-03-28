from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.infrastructure.db.models import (
    MissionActionType,
    MissionDifficulty,
    MissionProgressStatus,
    MissionType,
    PlanTier,
)


class MissionPromptRef(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str | None = None


class MissionLessonRef(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    min_tier: PlanTier
    locked: bool


class MissionRewardView(BaseModel):
    badge: str | None = None
    credits: int = 0
    premium_days: int = 0
    granted_at: datetime | None = None


class MissionNextStep(BaseModel):
    label: str
    href: str
    action: str


class MissionRead(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    description: str | None
    objective: str
    completion_condition: str
    difficulty: MissionDifficulty
    mission_type: MissionType
    action_type: MissionActionType
    is_repeatable: bool = False
    repeat_interval_days: int = 0
    status: MissionProgressStatus
    completion_count: int = 0
    progress_count: int
    required_count: int
    started_at: datetime | None = None
    last_event_at: datetime | None = None
    completed_at: datetime | None = None
    available_again_at: datetime | None = None
    prompts: list[MissionPromptRef]
    lesson: MissionLessonRef | None = None
    steps: list["MissionStepRead"] = []
    reward: MissionRewardView
    next_step: MissionNextStep | None = None


class MissionRewardSummary(BaseModel):
    credits: int
    badges: list[str]
    premium_unlock_until: datetime | None = None


class MissionStepRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    action_type: MissionActionType
    status: MissionProgressStatus
    progress_count: int
    required_count: int
    reward_credits: int = 0
    prompt: MissionPromptRef | None = None
    lesson: MissionLessonRef | None = None


class MissionListRead(BaseModel):
    missions: list[MissionRead]
    current_mission_slug: str | None = None
    completed_count: int
    total_count: int
    rewards: MissionRewardSummary


class MissionCurrentRead(BaseModel):
    current: MissionRead | None
    next: MissionRead | None
    latest_completed: MissionRead | None
    completed_count: int
    total_count: int
    rewards: MissionRewardSummary
