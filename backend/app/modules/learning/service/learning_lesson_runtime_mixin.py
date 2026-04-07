from __future__ import annotations

from app.core.errors import AppError, NotFoundError
from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import User
from app.modules.learning.content.catalog import find_lesson, get_course
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import LearningLessonRead, LearningLessonStatus
from app.modules.learning.service.learning_utils import first_incomplete_step_slug, safe_percent


class LearningLessonRuntimeMixin:
    async def lesson(
        self,
        *,
        user: User | None,
        course_slug: str,
        lesson_slug: str,
        language: SupportedLanguage,
    ) -> LearningLessonRead:
        course = get_course(course_slug)
        if course is None:
            raise NotFoundError("lesson", course_slug)

        total_lessons = self._total_lessons(course)
        lesson_resolution = self._resolve_lesson(course=course, lesson_slug=lesson_slug)
        course_progress, lesson_progress_rows, step_progress_rows = await self._load_lesson_progress(
            user=user,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            total_lessons=total_lessons,
        )

        lesson_progress_map = {row.lesson_slug: row for row in lesson_progress_rows}
        completed_lessons = {row.lesson_slug for row in lesson_progress_rows if row.status == "completed"}
        lesson_unlock_map = self._lesson_unlock_map(
            ordered_lessons=lesson_resolution.ordered_lessons,
            completed_lessons=completed_lessons,
        )
        if not lesson_unlock_map.get(lesson_slug, False):
            raise AppError(
                code="lesson_locked",
                message="Complete previous lessons to open this lesson.",
                status_code=409,
                message_key="errors.learning_lesson_locked",
            )

        steps_out, completed_steps = self._build_lesson_steps(
            lesson=lesson_resolution.lesson_row,
            step_progress_rows=step_progress_rows,
            language=language,
        )
        lesson_progress = lesson_progress_map.get(lesson_slug)
        lesson_status: LearningLessonStatus = (
            "completed"
            if lesson_progress is not None and lesson_progress.status == "completed"
            else ("in_progress" if lesson_progress is not None else "not_started")
        )
        lesson_progress_percent = int(lesson_progress.progress_percent) if lesson_progress is not None else 0
        course_progress_percent = (
            int(course_progress.progress_percent)
            if course_progress is not None
            else safe_percent(len(completed_lessons), total_lessons)
        )

        current_step_slug = first_incomplete_step_slug(lesson_resolution.lesson_row["steps"], completed_steps)
        if current_step_slug is None and lesson_resolution.lesson_row["steps"]:
            current_step_slug = lesson_resolution.lesson_row["steps"][-1]["slug"]

        lesson_list = self._build_lesson_outline(
            ordered_lessons=lesson_resolution.ordered_lessons,
            lesson_progress_rows=lesson_progress_rows,
            language=language,
            course_slug=course_slug,
        )
        previous_lesson_href, next_lesson_href = self._lesson_neighbors(
            ordered_lessons=lesson_resolution.ordered_lessons,
            lesson_slug=lesson_slug,
            course_slug=course_slug,
        )

        return LearningLessonRead(
            course_slug=course_slug,
            module_slug=lesson_resolution.module_row["slug"],
            lesson_slug=lesson_slug,
            title=pick_text(lesson_resolution.lesson_row["title"], language),
            summary=pick_text(lesson_resolution.lesson_row["summary"], language),
            objective=(
                pick_text(lesson_resolution.lesson_row["objective"], language)
                if lesson_resolution.lesson_row.get("objective")
                else None
            ),
            deliverable=(
                pick_text(lesson_resolution.lesson_row["deliverable"], language)
                if lesson_resolution.lesson_row.get("deliverable")
                else None
            ),
            scenario_title=(
                pick_text(lesson_resolution.lesson_row["scenario_title"], language)
                if lesson_resolution.lesson_row.get("scenario_title")
                else None
            ),
            scenario_body=(
                pick_text(lesson_resolution.lesson_row["scenario_body"], language)
                if lesson_resolution.lesson_row.get("scenario_body")
                else None
            ),
            debrief=[pick_text(item, language) for item in lesson_resolution.lesson_row.get("debrief", [])],
            review_rubric=[
                pick_text(item, language) for item in lesson_resolution.lesson_row.get("review_rubric", [])
            ],
            common_mistakes=[
                pick_text(item, language) for item in lesson_resolution.lesson_row.get("common_mistakes", [])
            ],
            estimated_minutes=int(lesson_resolution.lesson_row["estimated_minutes"]),
            position_in_course=lesson_resolution.lesson_index,
            total_lessons=total_lessons,
            progress_percent=lesson_progress_percent,
            course_progress_percent=course_progress_percent,
            status=lesson_status,
            unlocked=True,
            is_final_assessment=bool(lesson_resolution.lesson_row.get("is_final_assessment", False)),
            return_to_course_href=f"/learn/course/{course_slug}",
            previous_lesson_href=previous_lesson_href,
            next_lesson_href=next_lesson_href,
            steps=steps_out,
            current_step_slug=current_step_slug,
            lesson_list=lesson_list,
        )

    async def locate_lesson(self, lesson_slug: str) -> tuple[str, str] | None:
        row = find_lesson(lesson_slug)
        if row is None:
            return None
        course_slug, _module_slug, lesson = row
        return course_slug, lesson["slug"]
