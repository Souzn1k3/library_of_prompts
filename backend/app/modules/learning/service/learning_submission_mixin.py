from __future__ import annotations

from typing import Any

from app.core.errors import AppError
from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import User
from app.modules.learning.model.learning import LearningStepSubmitRead
from app.modules.learning.service.learning_submission_context_mixin import LearningSubmissionContextMixin
from app.modules.learning.service.learning_submission_progress_mixin import LearningSubmissionProgressMixin
from app.modules.learning.service.learning_submission_reward_mixin import LearningSubmissionRewardMixin
from app.modules.learning.service.learning_types import MissionServiceProtocol, RewardState, StoreServiceProtocol


class LearningSubmissionMixin(
    LearningSubmissionRewardMixin,
    LearningSubmissionProgressMixin,
    LearningSubmissionContextMixin,
):
    async def submit_step(
        self,
        *,
        user: User,
        course_slug: str,
        lesson_slug: str,
        step_slug: str,
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
        missions: MissionServiceProtocol,
        store: StoreServiceProtocol,
    ) -> LearningStepSubmitRead:
        ctx = self._resolve_submission_context(
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
        )
        await self._ensure_legacy_lessons()

        course_progress = await self._ensure_course_progress(
            user_id=user.id,
            course_slug=course_slug,
            total_lessons=self._total_lessons(ctx.course),
        )
        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
        completed_lessons = {row.lesson_slug for row in lesson_rows if row.status == "completed"}
        lesson_unlock_map = self._lesson_unlock_map(
            ordered_lessons=self._ordered_lessons(ctx.course),
            completed_lessons=completed_lessons,
        )
        if not lesson_unlock_map.get(lesson_slug, False):
            raise AppError(
                code="lesson_locked",
                message="Complete previous lessons to open this lesson.",
                status_code=409,
                message_key="errors.learning_lesson_locked",
            )

        step_rows_for_lesson = await self._repo.list_step_progress(
            user_id=user.id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        completed_steps = {row.step_slug for row in step_rows_for_lesson if row.passed}
        if not self._step_unlocked(ctx.lesson, step_slug, completed_steps):
            raise AppError(
                code="step_locked",
                message="Complete the current practice step before moving to the next one.",
                status_code=409,
                message_key="errors.step_locked",
            )

        step_progress = await self._ensure_step_progress(
            user_id=user.id,
            course_slug=course_slug,
            module_slug=ctx.module_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
            step_kind=ctx.step["kind"],
        )
        step_result = await self._evaluate_and_save_step_progress(
            step_progress=step_progress,
            step=ctx.step,
            answer=answer,
            language=language,
        )
        lesson_progress, lesson_completed_now = await self._update_lesson_progress(
            user_id=user.id,
            course_slug=course_slug,
            module_slug=ctx.module_slug,
            lesson_slug=lesson_slug,
            lesson=ctx.lesson,
            step_slug=step_slug,
            feedback=step_result.feedback,
        )
        submission = ctx.step.get("submission", {"type": "none"})
        course_progress, course_completed_now, lesson_for_resume, step_for_resume = await self._update_course_progress(
            user=user,
            course_slug=course_slug,
            course=ctx.course,
            course_progress=course_progress,
            submission=submission,
            passed=step_result.passed,
        )

        reward_state = RewardState()
        if lesson_completed_now and not lesson_progress.lmn_reward_granted:
            await self._apply_lesson_completion_reward(
                user=user,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
                step_slug=step_slug,
                lesson=ctx.lesson,
                course=ctx.course,
                lesson_progress=lesson_progress,
                missions=missions,
                store=store,
                reward_state=reward_state,
            )
        if course_completed_now:
            await self._apply_course_completion_reward(
                user=user,
                course_slug=course_slug,
                course=ctx.course,
                store=store,
                reward_state=reward_state,
            )

        resume_href = (
            f"/learn/course/{course_slug}/lesson/{lesson_for_resume}"
            if lesson_for_resume
            else f"/learn/course/{course_slug}"
        )
        weak_areas = self._localize_weak_areas(
            weak_area_counter=course_progress.weak_areas if isinstance(course_progress.weak_areas, dict) else {},
            language=language,
        )
        next_step_slug = step_for_resume if lesson_for_resume == lesson_slug else None

        return LearningStepSubmitRead(
            course_slug=course_slug,
            module_slug=ctx.module_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
            passed=step_result.passed,
            completed=bool(step_progress.passed),
            score=step_result.score,
            attempts=int(step_progress.attempts),
            feedback=step_result.feedback,
            lesson_progress_percent=int(lesson_progress.progress_percent),
            course_progress_percent=int(course_progress.progress_percent),
            lesson_completed=lesson_completed_now,
            course_completed=course_completed_now,
            next_step_slug=next_step_slug,
            next_lesson_slug=lesson_for_resume,
            resume_href=resume_href,
            weak_areas=weak_areas,
            awarded_lmn=reward_state.awarded_lmn,
            awarded_badge=reward_state.awarded_badge,
            certificate_ready=reward_state.certificate_ready,
            economy=reward_state.economy,
        )
