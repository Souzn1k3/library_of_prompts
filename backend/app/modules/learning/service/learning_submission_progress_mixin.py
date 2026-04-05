from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import LearningCourseProgress, LearningLessonProgress, LearningStepProgress, User
from app.modules.learning.model.learning import LearningStepFeedbackRead
from app.modules.learning.service.learning_types import StepEvaluationResult
from app.modules.learning.service.learning_utils import safe_percent


class LearningSubmissionProgressMixin:
    async def _evaluate_and_save_step_progress(
        self,
        *,
        step_progress: LearningStepProgress,
        step: dict,
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> StepEvaluationResult:
        submission = step.get("submission", {"type": "none"})
        passed, score, feedback = self._step_evaluator.evaluate(
            submission=submission,
            answer=answer,
            language=language,
        )
        now = datetime.now(timezone.utc)
        step_progress.attempts = int(step_progress.attempts) + 1
        step_progress.status = "completed" if passed else "in_progress"
        step_progress.passed = passed
        step_progress.last_score = score
        step_progress.best_score = max(int(step_progress.best_score), score)
        step_progress.answer_json = answer
        step_progress.feedback_json = feedback.model_dump()
        step_progress.last_activity_at = now
        if passed:
            step_progress.completed_at = now
        await self._repo.save_step_progress(step_progress)
        return StepEvaluationResult(passed=passed, score=score, feedback=feedback)

    async def _update_lesson_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        module_slug: str,
        lesson_slug: str,
        lesson: dict,
        step_slug: str,
        feedback: LearningStepFeedbackRead,
    ) -> tuple[LearningLessonProgress, bool]:
        lesson_progress = await self._ensure_lesson_progress(
            user_id=user_id,
            course_slug=course_slug,
            module_slug=module_slug,
            lesson_slug=lesson_slug,
            total_steps=self._total_steps(lesson),
        )
        all_step_rows = await self._repo.list_step_progress(
            user_id=user_id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        completed_steps = sum(1 for row in all_step_rows if row.passed)
        lesson_progress.total_steps = self._total_steps(lesson)
        lesson_progress.completed_steps = completed_steps
        lesson_progress.progress_percent = safe_percent(completed_steps, lesson_progress.total_steps)
        lesson_progress.status = "completed" if completed_steps >= lesson_progress.total_steps else "in_progress"
        lesson_progress.attempts_count = int(lesson_progress.attempts_count) + 1
        lesson_progress.last_step_slug = step_slug
        lesson_progress.last_feedback = feedback.model_dump()
        lesson_progress.last_activity_at = datetime.now(timezone.utc)
        lesson_completed_now = False
        if lesson_progress.status == "completed" and lesson_progress.completed_at is None:
            lesson_progress.completed_at = datetime.now(timezone.utc)
            lesson_completed_now = True
        await self._repo.save_lesson_progress(lesson_progress)
        return lesson_progress, lesson_completed_now

    async def _update_course_progress(
        self,
        *,
        user: User,
        course_slug: str,
        course: dict,
        course_progress: LearningCourseProgress,
        submission: dict[str, Any],
        passed: bool,
    ) -> tuple[LearningCourseProgress, bool, str | None, str | None]:
        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
        completed_lesson_count = sum(1 for row in lesson_rows if row.status == "completed")
        course_progress.completed_lessons = completed_lesson_count
        course_progress.total_lessons = self._total_lessons(course)
        course_progress.progress_percent = safe_percent(completed_lesson_count, course_progress.total_lessons)
        course_progress.status = "completed" if course_progress.progress_percent >= 100 else "active"
        course_completed_now = False
        if course_progress.status == "completed" and course_progress.completed_at is None:
            course_progress.completed_at = datetime.now(timezone.utc)
            course_completed_now = True

        weak_counter = dict(course_progress.weak_areas or {})
        if not passed:
            for tag in submission.get("weak_area_tags", []):
                weak_counter[str(tag)] = int(weak_counter.get(str(tag), 0)) + 1
        course_progress.weak_areas = weak_counter

        module_for_resume, lesson_for_resume, step_for_resume = await self._resume_pointer(
            user=user,
            course=course,
            course_row=course_progress,
        )
        course_progress.last_module_slug = module_for_resume
        course_progress.last_lesson_slug = lesson_for_resume
        course_progress.last_step_slug = step_for_resume
        course_progress.last_activity_at = datetime.now(timezone.utc)
        await self._repo.save_course_progress(course_progress)
        return course_progress, course_completed_now, lesson_for_resume, step_for_resume
