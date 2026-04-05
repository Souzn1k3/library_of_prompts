from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import LearningCourseProgress, LearningLessonProgress, User
from app.modules.learning.content.catalog import get_course
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import (
    LearningCourseRead,
    LearningCourseRewardsRead,
    LearningLessonOutlineRead,
    LearningLessonStatus,
    LearningModuleRead,
)
from app.modules.learning.service.learning_utils import safe_percent


class LearningReadCourseMixin:
    async def course(self, *, course_slug: str, user: User | None, language: SupportedLanguage) -> LearningCourseRead:
        course = get_course(course_slug)
        if course is None:
            raise NotFoundError("lesson", course_slug)

        row: LearningCourseProgress | None = None
        lesson_rows: list[LearningLessonProgress] = []
        weak_areas: list = []
        if user is not None:
            row = await self._repo.get_course_progress(user.id, course_slug)
            lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
            if row is not None and isinstance(row.weak_areas, dict):
                weak_areas = self._localize_weak_areas(weak_area_counter=row.weak_areas, language=language)

        lesson_row_map = {item.lesson_slug: item for item in lesson_rows}
        completed_lessons = {item.lesson_slug for item in lesson_rows if item.status == "completed"}
        status = self._status_from_row(row)
        total_lessons = self._total_lessons(course)
        progress_percent = int(row.progress_percent) if row is not None else safe_percent(len(completed_lessons), total_lessons)

        modules_out: list[LearningModuleRead] = []
        for module_pos, module in enumerate(course["modules"], start=1):
            lesson_out: list[LearningLessonOutlineRead] = []
            module_completed = 0
            for lesson_pos, lesson in enumerate(module["lessons"], start=1):
                lesson_row = lesson_row_map.get(lesson["slug"])
                lesson_status: LearningLessonStatus = (
                    "completed"
                    if lesson_row is not None and lesson_row.status == "completed"
                    else ("in_progress" if lesson_row is not None else "not_started")
                )
                if lesson_status == "completed":
                    module_completed += 1
                unlocked = self._lesson_unlocked(lesson, completed_lessons)
                lesson_out.append(
                    LearningLessonOutlineRead(
                        slug=lesson["slug"],
                        title=pick_text(lesson["title"], language),
                        summary=pick_text(lesson["summary"], language),
                        estimated_minutes=int(lesson["estimated_minutes"]),
                        position=lesson_pos,
                        status=lesson_status,
                        unlocked=unlocked,
                        is_final_assessment=bool(lesson.get("is_final_assessment", False)),
                        progress_percent=int(lesson_row.progress_percent) if lesson_row is not None else 0,
                        continue_href=f"/learn/course/{course_slug}/lesson/{lesson['slug']}",
                    )
                )

            modules_out.append(
                LearningModuleRead(
                    slug=module["slug"],
                    title=pick_text(module["title"], language),
                    summary=pick_text(module["summary"], language),
                    position=module_pos,
                    lesson_count=len(module["lessons"]),
                    progress_percent=safe_percent(module_completed, len(module["lessons"])),
                    lessons=lesson_out,
                )
            )

        resume_href: str | None = None
        if user is not None:
            _, lesson_slug, _ = await self._resume_pointer(user=user, course=course, course_row=row)
            if lesson_slug:
                resume_href = f"/learn/course/{course_slug}/lesson/{lesson_slug}"

        start_or_continue = {
            "completed": {"en": "Review course", "ru": "Повторить курс", "tt": "Курсны кабатлау"},
            "active": {"en": "Continue learning", "ru": "Продолжить обучение", "tt": "Укуны дәвам итү"},
            "not_started": {"en": "Start learning", "ru": "Начать обучение", "tt": "Өйрәнүне башлау"},
        }[status][language]

        rewards = LearningCourseRewardsRead(
            lesson_reward_lmn=int(course.get("lesson_default_reward_lmn", 0)),
            course_reward_lmn=int(course.get("course_reward_lmn", 0)),
            badge_code=str(course.get("badge_code", "")),
            certificate_template=str(course.get("certificate_template", "")),
            badge_earned=status == "completed",
            course_completed=status == "completed",
        )

        return LearningCourseRead(
            slug=course_slug,
            title=pick_text(course["title"], language),
            subtitle=pick_text(course["subtitle"], language),
            description=pick_text(course["description"], language),
            difficulty=course["difficulty"],
            estimated_minutes=int(course["estimated_minutes"]),
            module_count=len(course["modules"]),
            lesson_count=total_lessons,
            progress_percent=progress_percent,
            status=status,
            last_activity_at=row.last_activity_at if row is not None else None,
            resume_href=resume_href,
            start_or_continue_label=start_or_continue,
            what_you_will_learn=[pick_text(item, language) for item in course.get("what_you_will_learn", [])],
            modules=modules_out,
            rewards=rewards,
            weak_areas=weak_areas,
        )
