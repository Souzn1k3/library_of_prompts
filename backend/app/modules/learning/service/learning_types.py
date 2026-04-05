from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.infrastructure.db.models import User
from app.modules.economy.model.store import EconomyActionRead
from app.modules.learning.model.learning import LearningStepFeedbackRead


@dataclass(slots=True)
class LessonResolution:
    ordered_lessons: list[tuple[int, dict, int, dict, int]]
    module_row: dict
    lesson_row: dict
    lesson_index: int


@dataclass(slots=True)
class SubmissionContext:
    course: dict
    module_slug: str
    lesson: dict
    step: dict


@dataclass(slots=True)
class StepEvaluationResult:
    passed: bool
    score: int
    feedback: LearningStepFeedbackRead


@dataclass(slots=True)
class RewardState:
    awarded_lmn: int = 0
    awarded_badge: str | None = None
    certificate_ready: bool = False
    completed_mission_slugs: list[str] = field(default_factory=list)
    economy: EconomyActionRead | None = None


class MissionServiceProtocol(Protocol):
    async def record_event(
        self,
        *,
        user: User,
        event_type: str,
        prompt_id: uuid.UUID | None = None,
        lesson_id: uuid.UUID | None = None,
        source_event_key: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[str]: ...


class StoreServiceProtocol(Protocol):
    async def build_action_feedback(
        self,
        user: User,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead: ...
