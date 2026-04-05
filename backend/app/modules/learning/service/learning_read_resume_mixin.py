from __future__ import annotations

from app.infrastructure.db.models import LearningCourseProgress, User
from app.modules.learning.content.catalog import get_course, list_courses
from app.modules.learning.model.learning import LearningStartTargetRead
from app.modules.learning.service.learning_utils import first_incomplete_step_slug


class LearningReadResumeMixin:
    async def _resume_pointer(
        self,
        *,
        user: User,
        course: dict,
        course_row: LearningCourseProgress | None,
    ) -> tuple[str | None, str | None, str | None]:
        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course["slug"])
        completed_lessons = {row.lesson_slug for row in lesson_rows if row.status == "completed"}
        lesson_by_slug = {row.lesson_slug: row for row in lesson_rows}

        ordered = self._ordered_lessons(course)
        unlock_map = self._lesson_unlock_map(
            ordered_lessons=ordered,
            completed_lessons=completed_lessons,
        )
        for _, module, _, lesson, _ in ordered:
            if not unlock_map.get(lesson["slug"], False):
                continue
            lesson_row = lesson_by_slug.get(lesson["slug"])
            if lesson_row is None or lesson_row.status != "completed":
                step_rows = await self._repo.list_step_progress(
                    user_id=user.id,
                    course_slug=course["slug"],
                    lesson_slug=lesson["slug"],
                )
                completed_steps = {row.step_slug for row in step_rows if row.passed}
                step_slug = first_incomplete_step_slug(lesson["steps"], completed_steps)
                if step_slug is None and lesson["steps"]:
                    step_slug = lesson["steps"][0]["slug"]
                return module["slug"], lesson["slug"], step_slug

        if course_row is not None:
            return course_row.last_module_slug, course_row.last_lesson_slug, course_row.last_step_slug
        return None, None, None

    async def start_target(self, user: User | None) -> LearningStartTargetRead:
        if user is None:
            return LearningStartTargetRead(target="/learn", has_active_course=False)

        def first_lesson_target() -> LearningStartTargetRead:
            courses = list_courses()
            if not courses:
                return LearningStartTargetRead(target="/learn", has_active_course=False)
            course = courses[0]
            ordered = self._ordered_lessons(course)
            if not ordered:
                return LearningStartTargetRead(
                    target=f"/learn/course/{course['slug']}",
                    has_active_course=False,
                    active_course_slug=course["slug"],
                )
            first_lesson = ordered[0][3]["slug"]
            return LearningStartTargetRead(
                target=f"/learn/course/{course['slug']}/lesson/{first_lesson}",
                has_active_course=False,
                active_course_slug=course["slug"],
            )

        rows = await self._repo.list_course_progress(user.id)
        active = [row for row in rows if row.status != "completed" and int(row.progress_percent) < 100]
        if not active:
            return first_lesson_target()

        active.sort(key=lambda row: row.last_activity_at or row.started_at, reverse=True)
        top = active[0]
        course = get_course(top.course_slug)
        resume_href: str | None = None
        if course is not None:
            module_slug, lesson_slug, _step_slug = await self._resume_pointer(
                user=user,
                course=course,
                course_row=top,
            )
            if lesson_slug:
                resume_href = f"/learn/course/{top.course_slug}/lesson/{lesson_slug}"
            elif module_slug:
                resume_href = f"/learn/course/{top.course_slug}"

        return LearningStartTargetRead(
            target=resume_href or f"/learn/course/{top.course_slug}",
            has_active_course=True,
            active_course_slug=top.course_slug,
            resume_href=resume_href,
        )
