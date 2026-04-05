from __future__ import annotations

import uuid

from app.core.tiers import can_view_lesson
from app.infrastructure.db.models import (
    LessonMission,
    MissionProgressStatus,
    MissionStep,
    PromptStatus,
    User,
    UserMissionProgress,
    UserMissionStepProgress,
)
from app.modules.missions.model.mission import (
    MissionLessonRef,
    MissionPromptRef,
    MissionRead,
    MissionRewardView,
    MissionStepRead,
)
from app.modules.missions.service.mission_constants import STREAK_RECOVERY_MISSION_SLUG


class MissionReadProjectionMixin:
    def _mission_prompts(
        self,
        mission: LessonMission,
        *,
        can_view_premium: bool,
        fallback_prompts: list[MissionPromptRef],
    ) -> list[MissionPromptRef]:
        linked: list[MissionPromptRef] = []
        for link in sorted(mission.prompt_links, key=lambda row: row.sort_order):
            prompt = link.prompt
            if prompt is None or prompt.status != PromptStatus.published:
                continue
            if prompt.is_premium and not can_view_premium:
                continue
            linked.append(
                MissionPromptRef(
                    id=prompt.id,
                    slug=prompt.slug,
                    title=prompt.title,
                    summary=prompt.summary,
                )
            )
        return linked if linked else fallback_prompts

    def _step_read(
        self,
        step: MissionStep,
        *,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        user: User,
        can_view_premium: bool,
    ) -> MissionStepRead:
        progress = step_progress.get(step.id)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else self._policy.required_step_count(step)

        prompt = None
        if step.target_prompt:
            target_prompt = step.target_prompt
            if not target_prompt.is_premium or can_view_premium:
                prompt = MissionPromptRef(
                    id=target_prompt.id,
                    slug=target_prompt.slug,
                    title=target_prompt.title,
                    summary=target_prompt.summary,
                )

        lesson = None
        if step.target_lesson:
            target_lesson = step.target_lesson
            lesson = MissionLessonRef(
                id=target_lesson.id,
                slug=target_lesson.slug,
                title=target_lesson.title,
                min_tier=target_lesson.min_tier,
                locked=not can_view_lesson(user, target_lesson.min_tier),
            )

        return MissionStepRead(
            id=step.id,
            title=step.title,
            description=step.description,
            action_type=step.action_type,
            status=status,
            progress_count=progress_count,
            required_count=required_count,
            reward_credits=step.reward_credits,
            prompt=prompt,
            lesson=lesson,
        )

    def _mission_read(
        self,
        mission: LessonMission,
        progress: UserMissionProgress | None,
        *,
        user: User,
        segment: str,
        prompts: list[MissionPromptRef],
        lesson: MissionLessonRef | None,
        step_progress: dict[uuid.UUID, UserMissionStepProgress],
        can_view_premium: bool,
    ) -> MissionRead:
        available_again_at = self._policy.available_again_at(mission, progress)
        status = progress.status if progress else MissionProgressStatus.not_started
        progress_count = progress.progress_count if progress else 0
        required_count = progress.required_count if progress else self._policy.required_mission_count(mission)

        steps: list[MissionStepRead] = []
        if mission.steps:
            steps = [
                self._step_read(step, step_progress=step_progress, user=user, can_view_premium=can_view_premium)
                for step in mission.steps
            ]
            required_count, progress_count = self._policy.step_progress_totals(mission, step_progress)
            if progress_count >= required_count and required_count > 0:
                status = MissionProgressStatus.completed
        reward = MissionRewardView(
            badge=mission.reward_badge,
            credits=mission.reward_credits,
            premium_days=mission.reward_premium_days,
            granted_at=progress.reward_granted_at if progress else None,
        )
        next_step = self._mission_next_step(
            mission,
            prompts=prompts,
            lesson=lesson,
            status=status,
            step_progress=step_progress,
        )
        return MissionRead(
            id=mission.id,
            slug=mission.slug,
            title=mission.title,
            description=mission.description,
            objective=mission.objective,
            completion_condition=mission.completion_condition,
            difficulty=mission.difficulty,
            mission_type=mission.mission_type,
            action_type=mission.action_type,
            is_repeatable=mission.is_repeatable,
            repeat_interval_days=mission.repeat_interval_days,
            chain_id=mission.chain_id,
            chain_step=int(mission.chain_step),
            chain_total=int(mission.chain_total),
            chain_next_unlocked=bool(
                mission.chain_id
                and int(mission.chain_total) > 0
                and int(mission.chain_step) < int(mission.chain_total)
                and status == MissionProgressStatus.completed
            ),
            adaptive_reason=(
                "streak_recovery_window"
                if mission.slug == STREAK_RECOVERY_MISSION_SLUG
                else (mission.adaptive_segment or segment)
            ),
            synergy_bonus_preview=self._synergy_preview_for_mission(mission),
            status=status,
            completion_count=progress.completion_count if progress else 0,
            progress_count=min(progress_count, required_count),
            required_count=required_count,
            started_at=progress.started_at if progress else None,
            last_event_at=progress.last_event_at if progress else None,
            completed_at=progress.completed_at if progress else None,
            available_again_at=available_again_at,
            prompts=prompts,
            lesson=lesson,
            steps=steps,
            reward=reward,
            next_step=next_step,
        )
