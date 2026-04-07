from __future__ import annotations

from collections import Counter

from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import LearningCourseProgress, User
from app.modules.learning.content.catalog import list_courses
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import (
    LearningCatalogRead,
    LearningCourseCardRead,
    LearningMyCourseItemRead,
    LearningMyModulesRead,
    LearningProgressStatus,
)


class LearningReadCatalogMixin:
    async def catalog(self, *, user: User | None, language: SupportedLanguage) -> LearningCatalogRead:
        await self._ensure_legacy_lessons()
        courses = list_courses()
        progress_map: dict[str, LearningCourseProgress] = {}
        if user is not None:
            for row in await self._repo.list_course_progress(user.id):
                progress_map[row.course_slug] = row

        cards: list[LearningCourseCardRead] = []
        recommended: str | None = None

        for course in courses:
            row = progress_map.get(course["slug"])
            status = self._status_from_row(row)
            module_count = len(course["modules"])
            lesson_count = self._total_lessons(course)
            progress_percent = int(row.progress_percent) if row is not None else 0
            if recommended is None and status in {"active", "not_started"}:
                recommended = course["slug"]

            next_lesson_slug: str | None = None
            resume_href: str | None = None
            if user is not None and row is not None and status != "completed":
                _, next_lesson_slug, _ = await self._resume_pointer(user=user, course=course, course_row=row)
                if next_lesson_slug:
                    resume_href = f"/learn/course/{course['slug']}/lesson/{next_lesson_slug}"

            cards.append(
                LearningCourseCardRead(
                    slug=course["slug"],
                    title=pick_text(course["title"], language),
                    subtitle=pick_text(course["subtitle"], language),
                    description=pick_text(course["description"], language),
                    difficulty=course["difficulty"],
                    result_headline=pick_text(course["result_headline"], language)
                    if course.get("result_headline")
                    else None,
                    deliverable_preview=pick_text(course["deliverable_preview"], language)
                    if course.get("deliverable_preview")
                    else None,
                    estimated_minutes=int(course["estimated_minutes"]),
                    module_count=module_count,
                    lesson_count=lesson_count,
                    progress_percent=progress_percent,
                    status=status,
                    last_activity_at=row.last_activity_at if row is not None else None,
                    next_lesson_slug=next_lesson_slug,
                    resume_href=resume_href,
                    badge_earned=status == "completed",
                    course_reward_lmn=int(course.get("course_reward_lmn", 0)),
                )
            )

        if recommended is None and cards:
            recommended = cards[0].slug

        return LearningCatalogRead(courses=cards, recommended_course_slug=recommended)

    async def my_modules(self, *, user: User, language: SupportedLanguage) -> LearningMyModulesRead:
        courses = {course["slug"]: course for course in list_courses()}
        rows = await self._repo.list_course_progress(user.id)
        achievement_rows = await self._repo.list_achievements(user.id)
        achievement_codes = {row.achievement_code for row in achievement_rows}

        active_rows = [row for row in rows if row.course_slug in courses and self._status_from_row(row) != "completed"]
        completed_rows = [row for row in rows if row.course_slug in courses and self._status_from_row(row) == "completed"]

        active_rows.sort(key=lambda row: row.last_activity_at or row.started_at, reverse=True)
        completed_rows.sort(key=lambda row: row.completed_at or row.last_activity_at or row.started_at, reverse=True)

        weak_counter: Counter[str] = Counter()
        for row in active_rows:
            if isinstance(row.weak_areas, dict):
                for tag, count in row.weak_areas.items():
                    try:
                        weak_counter[str(tag)] += int(count)
                    except Exception:
                        continue

        async def to_item(row: LearningCourseProgress, status: LearningProgressStatus) -> LearningMyCourseItemRead:
            course = courses[row.course_slug]
            _, next_lesson_slug, _ = await self._resume_pointer(user=user, course=course, course_row=row)
            continue_href = (
                f"/learn/course/{course['slug']}/lesson/{next_lesson_slug}"
                if next_lesson_slug
                else f"/learn/course/{course['slug']}"
            )
            next_lesson_title = None
            if next_lesson_slug:
                for _, _, _, lesson, _ in self._ordered_lessons(course):
                    if lesson["slug"] == next_lesson_slug:
                        next_lesson_title = pick_text(lesson["title"], language)
                        break

            badge_code = course.get("badge_code") if status == "completed" else None
            certificate_ready = bool(badge_code and f"course:{course['slug']}:{badge_code}" in achievement_codes)
            return LearningMyCourseItemRead(
                slug=course["slug"],
                title=pick_text(course["title"], language),
                subtitle=pick_text(course["subtitle"], language),
                progress_percent=int(row.progress_percent),
                status=status,
                last_activity_at=row.last_activity_at,
                next_lesson_title=next_lesson_title,
                next_lesson_slug=next_lesson_slug,
                continue_href=continue_href,
                completed_at=row.completed_at,
                badge_code=badge_code,
                certificate_ready=certificate_ready,
            )

        active = [await to_item(row, "active") for row in active_rows]
        completed = [await to_item(row, "completed") for row in completed_rows]
        weak = self._localize_weak_areas(weak_area_counter=dict(weak_counter), language=language)
        return LearningMyModulesRead(active_courses=active, completed_courses=completed, weak_areas=weak)
