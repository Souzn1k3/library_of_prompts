from __future__ import annotations

import uuid

from app.infrastructure.db.models import (
    LessonMission,
    MissionActionType,
    MissionProgressStatus,
    UserMissionStepProgress,
)
from app.modules.missions.model.mission import MissionLessonRef, MissionNextStep, MissionPromptRef


class MissionReadNextStepMixin:
    def _mission_next_step(
        self,
        mission: LessonMission,
        *,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
        status: MissionProgressStatus,
        step_progress: dict[uuid.UUID, UserMissionStepProgress] | None = None,
    ) -> MissionNextStep | None:
        if mission.steps:
            step_progress = step_progress or {}
            pending = next(
                (
                    s
                    for s in mission.steps
                    if step_progress.get(s.id, None) is None
                    or step_progress[s.id].status != MissionProgressStatus.completed
                ),
                None,
            )
            if pending:
                if pending.target_prompt:
                    return MissionNextStep(
                        label=f"Try: {pending.title}",
                        href=f"/prompt/{pending.target_prompt.slug}",
                        action="open_step_prompt",
                    )
                if pending.target_lesson:
                    return MissionNextStep(
                        label=f"Open lesson: {pending.title}",
                        href=f"/learn/{pending.target_lesson.slug}",
                        action="open_step_lesson",
                    )
                return MissionNextStep(
                    label=f"Next step: {pending.title}",
                    href=f"/missions/{mission.slug}",
                    action="view_step",
                )

        if status == MissionProgressStatus.completed:
            return MissionNextStep(
                label="View result",
                href=f"/missions/{mission.slug}",
                action="view_result",
            )

        if mission.action_type == MissionActionType.onboarding_first_win:
            return MissionNextStep(label="Complete first win", href="/onboarding", action="finish_onboarding")

        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
        }:
            if prompts:
                return MissionNextStep(
                    label="Try linked prompt",
                    href=f"/prompt/{prompts[0].slug}",
                    action="open_prompt",
                )
            return MissionNextStep(label="Browse catalog", href="/catalog", action="browse_prompts")

        if mission.action_type == MissionActionType.lesson_completed:
            if lesson and lesson.locked:
                return MissionNextStep(
                    label="Unlock lesson",
                    href=f"/plans?tier={lesson.min_tier.value}",
                    action="upgrade_for_lesson",
                )
            if lesson:
                return MissionNextStep(
                    label="Continue lesson",
                    href=f"/learn/{lesson.slug}",
                    action="open_lesson",
                )
            return MissionNextStep(label="Browse lessons", href="/learn", action="browse_lessons")

        return MissionNextStep(label="Open mission details", href=f"/missions/{mission.slug}", action="details")

    def _synergy_preview_for_mission(self, mission: LessonMission) -> int:
        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
            MissionActionType.apply_prompt,
            MissionActionType.lesson_completed,
            MissionActionType.store_purchase,
        }:
            return 1
        return 0
