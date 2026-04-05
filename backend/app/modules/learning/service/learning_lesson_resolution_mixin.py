from __future__ import annotations

from app.core.errors import NotFoundError
from app.infrastructure.db.models import (
    LearningCourseProgress,
    LearningLessonProgress,
    LearningStepProgress,
    User,
)
from app.modules.learning.service.learning_types import LessonResolution


class LearningLessonResolutionMixin:
    def _resolve_lesson(self, *, course: dict, lesson_slug: str) -> LessonResolution:
        ordered = self._ordered_lessons(course)
        for _, module, _, lesson, global_index in ordered:
            if lesson["slug"] == lesson_slug:
                return LessonResolution(
                    ordered_lessons=ordered,
                    module_row=module,
                    lesson_row=lesson,
                    lesson_index=global_index,
                )
        raise NotFoundError("lesson", lesson_slug)

    async def _load_lesson_progress(
        self,
        *,
        user: User | None,
        course_slug: str,
        lesson_slug: str,
        total_lessons: int,
    ) -> tuple[LearningCourseProgress | None, list[LearningLessonProgress], list[LearningStepProgress]]:
        if user is None:
            return None, [], []
        course_progress = await self._ensure_course_progress(
            user_id=user.id,
            course_slug=course_slug,
            total_lessons=total_lessons,
        )
        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
        step_rows = await self._repo.list_step_progress(
            user_id=user.id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        return course_progress, lesson_rows, step_rows

    def _lesson_neighbors(
        self,
        *,
        ordered_lessons: list[tuple[int, dict, int, dict, int]],
        lesson_slug: str,
        course_slug: str,
    ) -> tuple[str | None, str | None]:
        lesson_slugs = [lesson["slug"] for _, _, _, lesson, _ in ordered_lessons]
        if lesson_slug not in lesson_slugs:
            return None, None
        idx = lesson_slugs.index(lesson_slug)
        previous_href = f"/learn/course/{course_slug}/lesson/{lesson_slugs[idx - 1]}" if idx > 0 else None
        next_href = (
            f"/learn/course/{course_slug}/lesson/{lesson_slugs[idx + 1]}"
            if idx < len(lesson_slugs) - 1
            else None
        )
        return previous_href, next_href
