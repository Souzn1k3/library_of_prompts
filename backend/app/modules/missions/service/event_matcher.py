import uuid

from app.infrastructure.db.models import (
    LessonMission,
    MissionActionType,
    MissionStep,
)


class MissionEventMatcher:
    def matches(
        self,
        mission: LessonMission,
        *,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        step: MissionStep | None = None,
    ) -> bool:
        action_type = step.action_type if step else mission.action_type
        linked_prompt_ids = (
            {step.target_prompt_id} if step and step.target_prompt_id else {link.prompt_id for link in mission.prompt_links}
        )
        if action_type == MissionActionType.copy_prompt:
            if event_type != "prompt_copied":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.save_prompt:
            if event_type != "prompt_saved":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.copy_or_save_prompt:
            if event_type not in {"prompt_copied", "prompt_saved"}:
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.apply_prompt:
            if event_type != "prompt_applied":
                return False
            if linked_prompt_ids and prompt_id not in linked_prompt_ids:
                return False
            return prompt_id is not None
        if action_type == MissionActionType.lesson_completed:
            if event_type != "lesson_completed":
                return False
            lesson_target = step.target_lesson_id if step else mission.lesson_id
            if lesson_target and lesson_id != lesson_target:
                return False
            return lesson_id is not None
        if action_type == MissionActionType.onboarding_first_win:
            return event_type == "onboarding_first_win_completed"
        if action_type == MissionActionType.manual_confirmation:
            return event_type == "mission_manual_confirmed"
        if action_type == MissionActionType.daily_checkin:
            return event_type == "daily_checkin"
        if action_type == MissionActionType.streak_activity:
            return event_type in {"streak_activity", "daily_checkin"}
        if action_type == MissionActionType.challenge_submission:
            return event_type == "challenge_submitted"
        if action_type == MissionActionType.store_purchase:
            return event_type == "store_purchase"
        if action_type == MissionActionType.multi_step:
            return event_type in {"mission_manual_confirmed", "mission_step_completed"}
        return False

    def matching_target_steps(
        self,
        mission: LessonMission,
        *,
        event_type: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
    ) -> list[MissionStep | None]:
        if mission.steps:
            return [
                step
                for step in mission.steps
                if self.matches(
                    mission,
                    event_type=event_type,
                    prompt_id=prompt_id,
                    lesson_id=lesson_id,
                    step=step,
                )
            ]
        if self.matches(
            mission,
            event_type=event_type,
            prompt_id=prompt_id,
            lesson_id=lesson_id,
        ):
            return [None]
        return []
