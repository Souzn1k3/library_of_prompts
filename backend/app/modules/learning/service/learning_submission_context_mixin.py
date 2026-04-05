from __future__ import annotations

from app.core.errors import NotFoundError
from app.modules.learning.content.catalog import get_course
from app.modules.learning.service.learning_types import SubmissionContext


class LearningSubmissionContextMixin:
    def _resolve_submission_context(
        self,
        *,
        course_slug: str,
        lesson_slug: str,
        step_slug: str,
    ) -> SubmissionContext:
        course = get_course(course_slug)
        if course is None:
            raise NotFoundError("lesson", course_slug)
        lesson_resolution = self._resolve_lesson(course=course, lesson_slug=lesson_slug)
        step = next((item for item in lesson_resolution.lesson_row["steps"] if item["slug"] == step_slug), None)
        if step is None:
            raise NotFoundError("lesson", step_slug)
        return SubmissionContext(
            course=course,
            module_slug=str(lesson_resolution.module_row["slug"]),
            lesson=lesson_resolution.lesson_row,
            step=step,
        )
