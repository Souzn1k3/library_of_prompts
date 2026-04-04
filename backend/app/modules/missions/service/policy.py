from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.infrastructure.db.models import (
    LessonMission,
    MissionProgressStatus,
    MissionStep,
    OnboardingProfile,
    UserMissionProgress,
    UserMissionStepProgress,
)


class MissionPolicy:
    def is_eligible(
        self,
        mission: LessonMission,
        profile: OnboardingProfile | None,
        *,
        segment: str = "balanced",
    ) -> bool:
        adaptive_segment = (mission.adaptive_segment or "").strip().lower()
        if adaptive_segment and adaptive_segment not in {"any", segment}:
            return False
        if profile is None:
            return mission.persona_role is None and mission.persona_goal is None
        if mission.persona_role is not None and profile.role != mission.persona_role:
            return False
        if mission.persona_goal is not None and profile.goal != mission.persona_goal:
            return False
        return True

    def persona_score(
        self,
        mission: LessonMission,
        profile: OnboardingProfile | None,
        *,
        segment: str = "balanced",
    ) -> int:
        if profile is None:
            base = 1 if mission.persona_role is None and mission.persona_goal is None else 0
        else:
            base = 0
            if mission.persona_role is None:
                base += 1
            elif profile.role == mission.persona_role:
                base += 3
            if mission.persona_goal is None:
                base += 1
            elif profile.goal == mission.persona_goal:
                base += 3

        adaptive_segment = (mission.adaptive_segment or "").strip().lower()
        if adaptive_segment and adaptive_segment == segment:
            base += 2
        return base

    def available_again_at(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
    ) -> datetime | None:
        if (
            progress is None
            or progress.completed_at is None
            or not mission.is_repeatable
            or mission.repeat_interval_days <= 0
        ):
            return None
        completed_at = (
            progress.completed_at
            if progress.completed_at.tzinfo is not None
            else progress.completed_at.replace(tzinfo=timezone.utc)
        )
        return completed_at + timedelta(days=mission.repeat_interval_days)

    def can_reset_cycle(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        now: datetime,
    ) -> bool:
        available_again_at = self.available_again_at(mission, progress)
        return bool(available_again_at is not None and available_again_at <= now)

    def required_step_count(self, step: MissionStep) -> int:
        return max(1, step.required_count)

    def required_mission_count(self, mission: LessonMission) -> int:
        return max(1, mission.required_count) if not mission.steps else sum(
            self.required_step_count(step) for step in mission.steps
        )

    def step_progress_totals(
        self,
        mission: LessonMission,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
    ) -> tuple[int, int]:
        total_required = total_progress = 0
        for step in mission.steps:
            required = self.required_step_count(step)
            row = step_progress.get(step.id)
            total_required += required
            total_progress += min(row.progress_count if row else 0, required)
        return total_required, min(total_required, total_progress)

    def is_chain_unlocked(
        self,
        mission: LessonMission,
        *,
        mission_by_slug: dict[str, LessonMission],
        progress_map: dict[uuid.UUID, UserMissionProgress],
    ) -> bool:
        unlock_slug = (mission.chain_unlock_on_slug or "").strip()
        if not unlock_slug:
            return True
        unlock_mission = mission_by_slug.get(unlock_slug)
        if unlock_mission is None:
            return True
        progress = progress_map.get(unlock_mission.id)
        if progress is None:
            return False
        return progress.completed_at is not None or progress.status == MissionProgressStatus.completed
