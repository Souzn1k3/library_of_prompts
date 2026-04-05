from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.db.models import LessonMission, UserMissionProgress, UserMissionStepProgress


@dataclass(slots=True)
class MissionEventContext:
    now: datetime
    segment: str
    mission_by_slug: dict[str, LessonMission]
    eligible_missions: list[LessonMission]
    mission_slug_by_id: dict[uuid.UUID, str]
    progress_map: dict[uuid.UUID, UserMissionProgress]
    step_progress_map: dict[uuid.UUID, UserMissionStepProgress]
