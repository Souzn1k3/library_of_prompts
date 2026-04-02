from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any

from app.core.errors import AppError, NotFoundError
from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LearningCourseProgress,
    LearningLessonProgress,
    LearningStepProgress,
    User,
)
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_service import StoreService
from app.modules.learning.content.catalog import find_lesson, get_course, list_courses
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import (
    LearningCatalogRead,
    LearningCourseCardRead,
    LearningCourseRead,
    LearningCourseRewardsRead,
    LearningLessonOutlineRead,
    LearningLessonRead,
    LearningLessonStatus,
    LearningLessonStepRead,
    LearningModuleRead,
    LearningMyCourseItemRead,
    LearningMyModulesRead,
    LearningProgressStatus,
    LearningStartTargetRead,
    LearningStepChoiceRead,
    LearningStepFeedbackRead,
    LearningStepSubmitRead,
    LearningWeakAreaRead,
)
from app.modules.learning.repository.learning_repository import LearningRepository
from app.modules.missions.service.mission_service import MissionService


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("\n", " ").split())


def _word_count(value: str) -> int:
    return len([part for part in value.replace("\n", " ").split(" ") if part.strip()])


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-zа-яё0-9]+", value.lower(), flags=re.IGNORECASE)


def _extract_marker_payload(text: str, marker: str) -> str:
    pattern = re.compile(
        re.escape(marker) + r"\s*[:\-]?\s*(.*?)(?=\s*\[[A-Z_]+\]|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matched = pattern.search(text)
    if not matched:
        return ""
    return matched.group(1).strip()


def _safe_percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round((done / total) * 100)))


def _first_incomplete_step_slug(steps: list[dict], completed_step_slugs: set[str]) -> str | None:
    for step in steps:
        if step["slug"] not in completed_step_slugs:
            return step["slug"]
    return None


class LearningService:
    def __init__(self, repo: LearningRepository, wallet_repo: WalletRepository) -> None:
        self._repo = repo
        self._wallet = wallet_repo

    def _ordered_lessons(self, course: dict) -> list[tuple[int, dict, int, dict, int]]:
        rows: list[tuple[int, dict, int, dict, int]] = []
        global_pos = 0
        for module_pos, module in enumerate(course["modules"], start=1):
            for lesson_pos, lesson in enumerate(module["lessons"], start=1):
                global_pos += 1
                rows.append((module_pos, module, lesson_pos, lesson, global_pos))
        return rows

    def _total_lessons(self, course: dict) -> int:
        return sum(len(module["lessons"]) for module in course["modules"])

    def _total_steps(self, lesson: dict) -> int:
        return len(lesson["steps"])

    def _lesson_unlocked(self, lesson: dict, completed_lessons: set[str]) -> bool:
        if not lesson.get("is_final_assessment", False):
            return True
        for req_slug in lesson.get("unlock_after_lessons", []):
            if req_slug not in completed_lessons:
                return False
        return True

    def _status_from_row(self, row: LearningCourseProgress | None) -> LearningProgressStatus:
        if row is None:
            return "not_started"
        if row.status == "completed" or int(row.progress_percent) >= 100:
            return "completed"
        return "active"

    def _localize_weak_areas(
        self,
        *,
        weak_area_counter: dict[str, int] | None,
        language: SupportedLanguage,
    ) -> list[LearningWeakAreaRead]:
        if not weak_area_counter:
            return []
        recommendations: dict[str, tuple[str, str | None]] = {
            "structure": (
                {
                    "en": "Revisit structured prompt markers.",
                    "ru": "Повторите структурные маркеры промпта.",
                    "tt": "Промпт структура маркерларын кабатлагыз.",
                }[language],
                "pe-structure-pattern",
            ),
            "constraints": (
                {
                    "en": "Practice constraints and example anchoring.",
                    "ru": "Потренируйте ограничения и якорные примеры.",
                    "tt": "Чикләү һәм мисал якорен кабатлагыз.",
                }[language],
                "pe-constraints-and-examples",
            ),
            "evaluation": (
                {
                    "en": "Use rubric-based quality checks before final output.",
                    "ru": "Добавляйте рубрику качества перед финальной выдачей.",
                    "tt": "Финалга кадәр рубрика буенча сыйфат тикшерегез.",
                }[language],
                "pe-evaluate-quality",
            ),
            "debugging": (
                {
                    "en": "Repeat the debugging workflow with one-block changes.",
                    "ru": "Повторите workflow отладки с изменением одного блока.",
                    "tt": "Бер блок үзгәртү белән төзәтү workflow-ны кабатлагыз.",
                }[language],
                "wf-prompt-debugging",
            ),
            "course-synthesis": (
                {
                    "en": "Run one full end-to-end workflow this week.",
                    "ru": "На этой неделе выполните один полный end-to-end workflow.",
                    "tt": "Бу атнада бер тулы end-to-end workflow эшләгез.",
                }[language],
                "wf-capstone",
            ),
        }
        items = sorted(weak_area_counter.items(), key=lambda item: item[1], reverse=True)[:4]
        out: list[LearningWeakAreaRead] = []
        for tag, count in items:
            recommendation, lesson_slug = recommendations.get(
                tag,
                (
                    {
                        "en": "Retry the latest practical step with stricter structure.",
                        "ru": "Повторите последнюю практику с более строгой структурой.",
                        "tt": "Соңгы практиканы катгыйрак структура белән кабатлагыз.",
                    }[language],
                    None,
                ),
            )
            out.append(
                LearningWeakAreaRead(
                    tag=tag,
                    count=int(count),
                    recommendation=recommendation,
                    lesson_slug=lesson_slug,
                )
            )
        return out

    async def _ensure_legacy_lessons(self, *, language: SupportedLanguage) -> None:
        courses = list_courses()
        sort_order = 100
        for course in courses:
            for _, _, _, lesson, _ in self._ordered_lessons(course):
                await self._repo.ensure_legacy_lesson(
                    slug=lesson["slug"],
                    title=pick_text(lesson["title"], language),
                    body=pick_text(lesson["summary"], language),
                    sort_order=sort_order,
                )
                sort_order += 1

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
        for _, module, _, lesson, _ in ordered:
            if not self._lesson_unlocked(lesson, completed_lessons):
                continue
            lesson_row = lesson_by_slug.get(lesson["slug"])
            if lesson_row is None or lesson_row.status != "completed":
                step_rows = await self._repo.list_step_progress(
                    user_id=user.id,
                    course_slug=course["slug"],
                    lesson_slug=lesson["slug"],
                )
                completed_steps = {row.step_slug for row in step_rows if row.passed}
                step_slug = _first_incomplete_step_slug(lesson["steps"], completed_steps)
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
        active = [
            row for row in rows if row.status != "completed" and int(row.progress_percent) < 100
        ]
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

    async def catalog(self, *, user: User | None, language: SupportedLanguage) -> LearningCatalogRead:
        await self._ensure_legacy_lessons(language=language)
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

        active_rows = [
            row for row in rows if row.course_slug in courses and self._status_from_row(row) != "completed"
        ]
        completed_rows = [
            row for row in rows if row.course_slug in courses and self._status_from_row(row) == "completed"
        ]

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
            certificate_ready = bool(
                badge_code and f"course:{course['slug']}:{badge_code}" in achievement_codes
            )
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

    async def course(self, *, course_slug: str, user: User | None, language: SupportedLanguage) -> LearningCourseRead:
        course = get_course(course_slug)
        if course is None:
            raise NotFoundError("lesson", course_slug)

        row: LearningCourseProgress | None = None
        lesson_rows: list[LearningLessonProgress] = []
        weak_areas: list[LearningWeakAreaRead] = []
        if user is not None:
            row = await self._repo.get_course_progress(user.id, course_slug)
            lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
            if row is not None and isinstance(row.weak_areas, dict):
                weak_areas = self._localize_weak_areas(weak_area_counter=row.weak_areas, language=language)

        lesson_row_map = {item.lesson_slug: item for item in lesson_rows}
        completed_lessons = {item.lesson_slug for item in lesson_rows if item.status == "completed"}
        status = self._status_from_row(row)
        total_lessons = self._total_lessons(course)
        progress_percent = int(row.progress_percent) if row is not None else _safe_percent(len(completed_lessons), total_lessons)

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
                    progress_percent=_safe_percent(module_completed, len(module["lessons"])),
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

        ordered = self._ordered_lessons(course)
        lesson_row: dict | None = None
        module_row: dict | None = None
        lesson_index = 0
        for _, module, _, lesson, global_index in ordered:
            if lesson["slug"] == lesson_slug:
                lesson_row = lesson
                module_row = module
                lesson_index = global_index
                break
        if lesson_row is None or module_row is None:
            raise NotFoundError("lesson", lesson_slug)

        course_progress: LearningCourseProgress | None = None
        lesson_progress_rows: list[LearningLessonProgress] = []
        step_progress_rows: list[LearningStepProgress] = []
        if user is not None:
            course_progress = await self._repo.get_course_progress(user.id, course_slug)
            if course_progress is None:
                course_progress = LearningCourseProgress(
                    user_id=user.id,
                    course_slug=course_slug,
                    total_lessons=self._total_lessons(course),
                    progress_percent=0,
                    status="active",
                    started_at=datetime.now(timezone.utc),
                )
                self._repo._session.add(course_progress)
            lesson_progress_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
            step_progress_rows = await self._repo.list_step_progress(
                user_id=user.id,
                course_slug=course_slug,
                lesson_slug=lesson_slug,
            )

        lesson_progress_map = {row.lesson_slug: row for row in lesson_progress_rows}
        completed_lessons = {row.lesson_slug for row in lesson_progress_rows if row.status == "completed"}
        unlocked = self._lesson_unlocked(lesson_row, completed_lessons)
        if not unlocked:
            raise AppError(
                code="lesson_locked",
                message="Complete prerequisite lessons to open this assessment.",
                status_code=409,
                message_key="errors.lesson_locked",
            )

        step_progress_map = {row.step_slug: row for row in step_progress_rows}
        completed_steps = {row.step_slug for row in step_progress_rows if row.passed}
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
            else _safe_percent(len(completed_lessons), self._total_lessons(course))
        )

        steps_out: list[LearningLessonStepRead] = []
        for step in lesson_row["steps"]:
            submission = step.get("submission", {"type": "none"})
            submission_type = submission.get("type", "none")
            row = step_progress_map.get(step["slug"])
            feedback = None
            if row is not None and isinstance(row.feedback_json, dict):
                feedback = LearningStepFeedbackRead.model_validate(row.feedback_json)
            steps_out.append(
                LearningLessonStepRead(
                    slug=step["slug"],
                    kind=step["kind"],
                    title=pick_text(step["title"], language),
                    estimated_minutes=int(step.get("estimated_minutes", 4)),
                    content=[pick_text(item, language) for item in step.get("content", [])],
                    task=pick_text(step["task"], language) if step.get("task") else None,
                    placeholder=pick_text(step["placeholder"], language) if step.get("placeholder") else None,
                    question=pick_text(submission["question"], language) if submission.get("question") else None,
                    choices=[
                        LearningStepChoiceRead(id=choice["id"], text=pick_text(choice["text"], language))
                        for choice in submission.get("choices", [])
                    ],
                    pass_score=int(submission.get("pass_score", 0)),
                    submission_type=submission_type,
                    unlocked=True,
                    completed=bool(row.passed) if row is not None else False,
                    attempts=int(row.attempts) if row is not None else 0,
                    last_score=int(row.last_score) if row is not None else None,
                    feedback=feedback,
                )
            )

        current_step_slug = _first_incomplete_step_slug(lesson_row["steps"], completed_steps)
        if current_step_slug is None and lesson_row["steps"]:
            current_step_slug = lesson_row["steps"][-1]["slug"]

        lesson_list: list[LearningLessonOutlineRead] = []
        for _, _module, lesson_pos, lesson, _global_pos in ordered:
            row = lesson_progress_map.get(lesson["slug"])
            status: LearningLessonStatus = (
                "completed"
                if row is not None and row.status == "completed"
                else ("in_progress" if row is not None else "not_started")
            )
            lesson_list.append(
                LearningLessonOutlineRead(
                    slug=lesson["slug"],
                    title=pick_text(lesson["title"], language),
                    summary=pick_text(lesson["summary"], language),
                    estimated_minutes=int(lesson["estimated_minutes"]),
                    position=lesson_pos,
                    status=status,
                    unlocked=self._lesson_unlocked(lesson, completed_lessons),
                    is_final_assessment=bool(lesson.get("is_final_assessment", False)),
                    progress_percent=int(row.progress_percent) if row is not None else 0,
                    continue_href=f"/learn/course/{course_slug}/lesson/{lesson['slug']}",
                )
            )

        previous_lesson_href = None
        next_lesson_href = None
        lesson_slugs = [lesson["slug"] for _, _, _, lesson, _ in ordered]
        if lesson_slug in lesson_slugs:
            idx = lesson_slugs.index(lesson_slug)
            if idx > 0:
                previous_lesson_href = f"/learn/course/{course_slug}/lesson/{lesson_slugs[idx - 1]}"
            if idx < len(lesson_slugs) - 1:
                next_lesson_href = f"/learn/course/{course_slug}/lesson/{lesson_slugs[idx + 1]}"

        return LearningLessonRead(
            course_slug=course_slug,
            module_slug=module_row["slug"],
            lesson_slug=lesson_slug,
            title=pick_text(lesson_row["title"], language),
            summary=pick_text(lesson_row["summary"], language),
            estimated_minutes=int(lesson_row["estimated_minutes"]),
            position_in_course=lesson_index,
            total_lessons=self._total_lessons(course),
            progress_percent=lesson_progress_percent,
            course_progress_percent=course_progress_percent,
            status=lesson_status,
            unlocked=True,
            is_final_assessment=bool(lesson_row.get("is_final_assessment", False)),
            return_to_course_href=f"/learn/course/{course_slug}",
            previous_lesson_href=previous_lesson_href,
            next_lesson_href=next_lesson_href,
            steps=steps_out,
            current_step_slug=current_step_slug,
            lesson_list=lesson_list,
        )

    def _feedback_message(self, *, language: SupportedLanguage, key: str) -> str:
        return {
            "passed": {
                "en": "Good result. Your structure is clear enough to execute.",
                "ru": "Хороший результат. Структура уже достаточно четкая для выполнения.",
                "tt": "Яхшы нәтиҗә. Структура башкару өчен җитәрлек ачык.",
            },
            "too_short": {
                "en": "Add more concrete detail.",
                "ru": "Добавьте больше конкретики.",
                "tt": "Күбрәк конкрет деталь өстәгез.",
            },
            "missing_markers": {
                "en": "Required structural markers are missing.",
                "ru": "Не хватает обязательных структурных маркеров.",
                "tt": "Мәҗбүри структура маркерлары җитми.",
            },
            "forbidden": {
                "en": "Avoid vague phrases that weaken control.",
                "ru": "Уберите размытые формулировки, они ослабляют контроль.",
                "tt": "Контрольне зәгыйфьләндергән томан сүзләрне алыгыз.",
            },
            "wrong_choice": {
                "en": "Not yet. Re-check why this option is tempting but weak.",
                "ru": "Пока нет. Перепроверьте, почему этот вариант кажется верным, но слабый.",
                "tt": "Әлегә юк. Бу вариант нигә җәлеп итүен, ләкин зәгыйфь булуын яңадан тикшерегез.",
            },
        }[key][language]
    def _validate_text_submission(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]:
        text = str((answer or {}).get("text") or "").strip()
        normalized = _normalize_text(text)
        min_words = int(submission.get("min_words", 1))
        required_markers = [str(marker) for marker in submission.get("required_markers", [])]
        bonus_markers = [str(marker) for marker in submission.get("bonus_markers", [])]
        forbidden = [str(marker) for marker in submission.get("forbidden_phrases", [])]
        pass_score = int(submission.get("pass_score", 70))

        wc = _word_count(text)
        missing_markers = [marker for marker in required_markers if marker.lower() not in normalized]
        bonus_hits = [marker for marker in bonus_markers if marker.lower() in normalized]
        forbidden_hits = [marker for marker in forbidden if marker.lower() in normalized]
        marker_payload_words: dict[str, int] = {}
        for marker in required_markers:
            payload = _extract_marker_payload(text, marker)
            marker_payload_words[marker] = _word_count(payload)
        empty_markers = [
            marker
            for marker, count in marker_payload_words.items()
            if marker not in missing_markers and count < 3
        ]

        tokens = _tokenize(text)
        unique_ratio = (len(set(tokens)) / len(tokens)) if tokens else 0.0
        token_counter = Counter(tokens)
        most_common_share = (
            token_counter.most_common(1)[0][1] / len(tokens)
            if tokens
            else 0.0
        )
        cue_hits = sum(
            1
            for cue in [
                "example",
                "пример",
                "format",
                "формат",
                "constraint",
                "огранич",
                "criterion",
                "критер",
                "step",
                "шаг",
                "audience",
                "аудит",
                "risk",
                "риск",
            ]
            if cue in normalized
        )
        has_numbering = bool(re.search(r"\b\d+[\).:\-]?", text))

        length_score = 25 if wc >= min_words else round((wc / max(min_words, 1)) * 25)
        if required_markers:
            per_marker = 25 / len(required_markers)
            structure_score = round(per_marker * (len(required_markers) - len(missing_markers)))
            completeness_score = round(
                (20 / len(required_markers))
                * sum(1 for marker in required_markers if marker not in missing_markers and marker not in empty_markers)
            )
        else:
            structure_score = 25
            completeness_score = 20

        specificity_score = 0
        specificity_score += min(10, round(unique_ratio * 14))
        specificity_score += min(8, cue_hits * 2)
        specificity_score += 2 if has_numbering else 0
        specificity_score = min(20, specificity_score)

        bonus_score = min(10, len(bonus_hits) * 3)
        penalty = min(25, len(forbidden_hits) * 10)
        if empty_markers:
            penalty += min(18, len(empty_markers) * 6)
        if most_common_share > 0.2:
            penalty += 8
        if wc > 0 and wc < (min_words + 6) and len(required_markers) >= 4 and len(empty_markers) >= 2:
            penalty += 8

        score = max(
            0,
            min(
                100,
                length_score + structure_score + completeness_score + specificity_score + bonus_score - penalty,
            ),
        )
        passed = (
            score >= pass_score
            and not missing_markers
            and not empty_markers
            and wc >= min_words
            and not forbidden_hits
        )

        strengths: list[str] = []
        improvements: list[str] = []
        revisit: list[str] = []

        if wc >= min_words:
            strengths.append(
                {
                    "en": f"Detail level is sufficient ({wc} words).",
                    "ru": f"Уровень детализации достаточный ({wc} слов).",
                    "tt": f"Деталь дәрәҗәсе җитә ({wc} сүз).",
                }[language]
            )
        else:
            improvements.append(
                f"{self._feedback_message(language=language, key='too_short')} "
                + {
                    "en": f"Minimum: {min_words} words.",
                    "ru": f"Минимум: {min_words} слов.",
                    "tt": f"Минимум: {min_words} сүз.",
                }[language]
            )

        if not missing_markers:
            strengths.append(
                {
                    "en": "Required structural markers are present.",
                    "ru": "Все обязательные структурные маркеры на месте.",
                    "tt": "Барлык мәҗбүри структура маркерлары бар.",
                }[language]
            )
        else:
            improvements.append(
                f"{self._feedback_message(language=language, key='missing_markers')} "
                + {
                    "en": "Missing: ",
                    "ru": "Не хватает: ",
                    "tt": "Җитми: ",
                }[language]
                + ", ".join(missing_markers)
            )

        if empty_markers:
            improvements.append(
                {
                    "en": "Some markers are present but not filled with concrete detail: ",
                    "ru": "Некоторые маркеры указаны, но не заполнены конкретикой: ",
                    "tt": "Кайбер маркерлар бар, ләкин конкрет мәгълүмат юк: ",
                }[language]
                + ", ".join(empty_markers)
            )

        if bonus_hits:
            strengths.append(
                {
                    "en": "You added quality anchors: ",
                    "ru": "Вы добавили якоря качества: ",
                    "tt": "Сез сыйфат якорьларын өстәдегез: ",
                }[language]
                + ", ".join(bonus_hits)
            )

        if forbidden_hits:
            improvements.append(
                f"{self._feedback_message(language=language, key='forbidden')} "
                + ", ".join(forbidden_hits)
            )
            revisit.append(
                {
                    "en": "Review constraints and output format specificity.",
                    "ru": "Повторите раздел про ограничения и точность формата.",
                    "tt": "Чикләү һәм формат төгәллеге бүлеген кабатлагыз.",
                }[language]
            )

        verdict = (
            {
                "en": "Passed",
                "ru": "Пройдено",
                "tt": "Үтте",
            }[language]
            if passed
            else {
                "en": "Needs revision",
                "ru": "Нужна доработка",
                "tt": "Яхшырту кирәк",
            }[language]
        )
        feedback = LearningStepFeedbackRead(
            verdict=verdict,
            score=score,
            pass_score=pass_score,
            strengths=strengths if strengths else [self._feedback_message(language=language, key="passed")],
            improvements=improvements,
            revisit=revisit,
            hint=(
                {
                    "en": "Keep one idea per marker and avoid vague wording.",
                    "ru": "Заполняйте каждый маркер конкретным действием, ограничением и форматом результата.",
                    "tt": "Һәр маркерда бер ачык фикер калдырыгыз һәм томан сүзләрдән сакланыгыз.",
                }[language]
            ),
        )
        return passed, score, feedback

    def _validate_choice_submission(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]:
        selected = str((answer or {}).get("choice_id") or "").strip().lower()
        correct_ids = {str(item).lower() for item in submission.get("correct_choices", [])}
        pass_score = int(submission.get("pass_score", 100))
        choice_map = {str(item["id"]).lower(): item for item in submission.get("choices", [])}
        passed = selected in correct_ids and selected != ""
        score = 100 if passed else 35

        selected_expl = None
        if selected and selected in choice_map:
            selected_expl = choice_map[selected].get("explanation")
        correct_expl = None
        for cid in correct_ids:
            if cid in choice_map:
                correct_expl = choice_map[cid].get("explanation")
                break

        strengths = []
        improvements = []
        if passed:
            strengths.append(
                pick_text(correct_expl, language)
                if isinstance(correct_expl, dict)
                else self._feedback_message(language=language, key="passed")
            )
        else:
            improvements.append(self._feedback_message(language=language, key="wrong_choice"))
            if isinstance(selected_expl, dict):
                improvements.append(pick_text(selected_expl, language))
            if isinstance(correct_expl, dict):
                improvements.append(
                    {
                        "en": "What to keep in mind: ",
                        "ru": "Что важно учитывать: ",
                        "tt": "Нәрсәне истә тотарга: ",
                    }[language]
                    + pick_text(correct_expl, language)
                )

        feedback = LearningStepFeedbackRead(
            verdict={True: {"en": "Correct", "ru": "Верно", "tt": "Дөрес"}, False: {"en": "Incorrect", "ru": "Неверно", "tt": "Дөрес түгел"}}[passed][language],
            score=score,
            pass_score=pass_score,
            strengths=strengths,
            improvements=improvements,
            revisit=[] if passed else [{
                "en": "Revisit the lesson micro-theory before retry.",
                "ru": "Перед повтором вернитесь к микро-теории урока.",
                "tt": "Кабатлаганчы дәреснең микро-теориясен яңадан карагыз.",
            }[language]],
            hint=None,
        )
        return passed, score, feedback
    async def submit_step(
        self,
        *,
        user: User,
        course_slug: str,
        lesson_slug: str,
        step_slug: str,
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
        missions: MissionService,
        store: StoreService,
    ) -> LearningStepSubmitRead:
        course = get_course(course_slug)
        if course is None:
            raise NotFoundError("lesson", course_slug)

        module_slug: str | None = None
        lesson: dict | None = None
        for _module in course["modules"]:
            for _lesson in _module["lessons"]:
                if _lesson["slug"] == lesson_slug:
                    lesson = _lesson
                    module_slug = _module["slug"]
                    break
            if lesson is not None:
                break
        if lesson is None or module_slug is None:
            raise NotFoundError("lesson", lesson_slug)

        step = next((item for item in lesson["steps"] if item["slug"] == step_slug), None)
        if step is None:
            raise NotFoundError("lesson", step_slug)

        await self._ensure_legacy_lessons(language=language)

        course_progress = await self._repo.get_course_progress(user.id, course_slug)
        if course_progress is None:
            course_progress = LearningCourseProgress(
                user_id=user.id,
                course_slug=course_slug,
                status="active",
                total_lessons=self._total_lessons(course),
                completed_lessons=0,
                progress_percent=0,
                started_at=datetime.now(timezone.utc),
            )
            self._repo._session.add(course_progress)
            await self._repo.save_course_progress(course_progress)

        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
        completed_lessons = {row.lesson_slug for row in lesson_rows if row.status == "completed"}
        if not self._lesson_unlocked(lesson, completed_lessons):
            raise AppError(
                code="lesson_locked",
                message="Complete prerequisite lessons to open this assessment.",
                status_code=409,
                message_key="errors.lesson_locked",
            )

        step_progress = await self._repo.get_step_progress(
            user_id=user.id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
        )
        if step_progress is None:
            step_progress = LearningStepProgress(
                user_id=user.id,
                course_slug=course_slug,
                module_slug=module_slug,
                lesson_slug=lesson_slug,
                step_slug=step_slug,
                step_kind=step["kind"],
                status="not_started",
            )
            self._repo._session.add(step_progress)
            await self._repo.save_step_progress(step_progress)

        submission = step.get("submission", {"type": "none"})
        submission_type = submission.get("type", "none")
        if submission_type == "none":
            passed, score, feedback = True, 100, LearningStepFeedbackRead(
                verdict={"en": "Completed", "ru": "Завершено", "tt": "Тәмам"}[language],
                score=100,
                pass_score=100,
                strengths=[{"en": "Step marked as completed.", "ru": "Шаг отмечен завершенным.", "tt": "Адым тәмамланды дип билгеләнде."}[language]],
                improvements=[],
                revisit=[],
                hint=None,
            )
        elif submission_type == "choice":
            passed, score, feedback = self._validate_choice_submission(
                submission=submission,
                answer=answer,
                language=language,
            )
        else:
            passed, score, feedback = self._validate_text_submission(
                submission=submission,
                answer=answer,
                language=language,
            )

        step_progress.attempts = int(step_progress.attempts) + 1
        step_progress.status = "completed" if passed else "in_progress"
        step_progress.passed = passed
        step_progress.last_score = score
        step_progress.best_score = max(int(step_progress.best_score), score)
        step_progress.answer_json = answer
        step_progress.feedback_json = feedback.model_dump()
        step_progress.last_activity_at = datetime.now(timezone.utc)
        if passed:
            step_progress.completed_at = datetime.now(timezone.utc)
        await self._repo.save_step_progress(step_progress)

        lesson_progress = await self._repo.get_lesson_progress(
            user_id=user.id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        if lesson_progress is None:
            lesson_progress = LearningLessonProgress(
                user_id=user.id,
                course_slug=course_slug,
                module_slug=module_slug,
                lesson_slug=lesson_slug,
                total_steps=self._total_steps(lesson),
                status="in_progress",
            )
            self._repo._session.add(lesson_progress)
            await self._repo.save_lesson_progress(lesson_progress)

        all_step_rows = await self._repo.list_step_progress(
            user_id=user.id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        completed_steps = sum(1 for row in all_step_rows if row.passed)
        lesson_progress.total_steps = self._total_steps(lesson)
        lesson_progress.completed_steps = completed_steps
        lesson_progress.progress_percent = _safe_percent(completed_steps, lesson_progress.total_steps)
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

        lesson_rows = await self._repo.list_lesson_progress(user_id=user.id, course_slug=course_slug)
        completed_lesson_count = sum(1 for row in lesson_rows if row.status == "completed")
        course_progress.completed_lessons = completed_lesson_count
        course_progress.total_lessons = self._total_lessons(course)
        course_progress.progress_percent = _safe_percent(completed_lesson_count, course_progress.total_lessons)
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

        awarded_lmn = 0
        awarded_badge: str | None = None
        certificate_ready = False
        completed_mission_slugs: list[str] = []
        economy = None

        if lesson_completed_now and not lesson_progress.lmn_reward_granted:
            lesson_reward = int(lesson.get("reward_lmn", course.get("lesson_default_reward_lmn", 0)))
            reward_key = f"lesson:{course_slug}:{lesson_slug}"
            if await self._repo.grant_reward(
                user_id=user.id,
                grant_key=reward_key,
                reward_type="lesson_completion",
                course_slug=course_slug,
                lesson_slug=lesson_slug,
                lmn_amount=lesson_reward,
                meta={"step_slug": step_slug},
            ):
                previous_balance, _, _ = await self._wallet.summary(user.id)
                await self._wallet.adjust_balance(
                    user_id=user.id,
                    amount=lesson_reward,
                    reason=CurrencyTransactionType.mission_reward,
                    context=f"learning:lesson:{course_slug}:{lesson_slug}",
                    source_id=uuid.uuid5(uuid.NAMESPACE_URL, reward_key),
                    metadata={"course_slug": course_slug, "lesson_slug": lesson_slug},
                )
                awarded_lmn += lesson_reward
                lesson_progress.lmn_reward_granted = True
                await self._repo.save_lesson_progress(lesson_progress)

                legacy_lesson = await self._repo.get_legacy_lesson_by_slug(lesson_slug)
                if legacy_lesson is not None:
                    completed_mission_slugs = await missions.record_event(
                        user=user,
                        event_type="lesson_completed",
                        lesson_id=legacy_lesson.id,
                        source_event_key=f"learning_lesson_completed:{user.id}:{course_slug}:{lesson_slug}",
                    )
                completed_mission_slugs.extend(
                    await missions.record_event(
                        user=user,
                        event_type="streak_activity",
                        source_event_key=f"learning_streak:{user.id}:{datetime.now(timezone.utc).date().isoformat()}",
                        payload={"source": "learning_lesson_completed", "course_slug": course_slug},
                    )
                )
                economy = await store.build_action_feedback(
                    user,
                    previous_balance=previous_balance,
                    completed_mission_slugs=list(dict.fromkeys(completed_mission_slugs)),
                )

        if course_completed_now:
            course_reward = int(course.get("course_reward_lmn", 0))
            reward_key = f"course:{course_slug}"
            if await self._repo.grant_reward(
                user_id=user.id,
                grant_key=reward_key,
                reward_type="course_completion",
                course_slug=course_slug,
                lesson_slug=None,
                lmn_amount=course_reward,
                meta={"completed_at": datetime.now(timezone.utc).isoformat()},
            ):
                previous_balance, _, _ = await self._wallet.summary(user.id)
                await self._wallet.adjust_balance(
                    user_id=user.id,
                    amount=course_reward,
                    reason=CurrencyTransactionType.mission_reward,
                    context=f"learning:course:{course_slug}",
                    source_id=uuid.uuid5(uuid.NAMESPACE_URL, reward_key),
                    metadata={"course_slug": course_slug, "reward_type": "course_completion"},
                )
                awarded_lmn += course_reward
                awarded_badge = str(course.get("badge_code"))
                await self._repo.grant_achievement(
                    user_id=user.id,
                    achievement_code=f"course:{course_slug}:{awarded_badge}",
                    course_slug=course_slug,
                    payload={
                        "badge_code": awarded_badge,
                        "certificate_template": course.get("certificate_template"),
                    },
                )
                certificate_ready = True
                economy = await store.build_action_feedback(
                    user,
                    previous_balance=previous_balance,
                    completed_mission_slugs=list(dict.fromkeys(completed_mission_slugs)),
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
        next_step_slug = None
        if lesson_for_resume == lesson_slug:
            next_step_slug = step_for_resume

        return LearningStepSubmitRead(
            course_slug=course_slug,
            module_slug=module_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
            passed=passed,
            completed=bool(step_progress.passed),
            score=score,
            attempts=int(step_progress.attempts),
            feedback=feedback,
            lesson_progress_percent=int(lesson_progress.progress_percent),
            course_progress_percent=int(course_progress.progress_percent),
            lesson_completed=lesson_completed_now,
            course_completed=course_completed_now,
            next_step_slug=next_step_slug,
            next_lesson_slug=lesson_for_resume,
            resume_href=resume_href,
            weak_areas=weak_areas,
            awarded_lmn=awarded_lmn,
            awarded_badge=awarded_badge,
            certificate_ready=certificate_ready,
            economy=economy,
        )

    async def locate_lesson(self, lesson_slug: str) -> tuple[str, str] | None:
        row = find_lesson(lesson_slug)
        if row is None:
            return None
        course_slug, _module_slug, lesson = row
        return course_slug, lesson["slug"]
