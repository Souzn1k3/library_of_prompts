from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import (
    LearningCourseProgress,
    LearningLessonProgress,
    LearningStepProgress,
)
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.learning.content.catalog import list_courses
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import (
    LearningProgressStatus,
    LearningWeakAreaRead,
)
from app.modules.learning.repository.learning_repository import LearningRepository
from app.modules.learning.service.learning_lesson_mixin import LearningLessonMixin
from app.modules.learning.service.learning_read_mixin import LearningReadMixin
from app.modules.learning.service.learning_submission_mixin import LearningSubmissionMixin
from app.modules.learning.service.step_evaluator import (
    LearningStepSubmissionEvaluator,
    LearningStepSubmissionEvaluatorProtocol,
)


class LearningService(LearningReadMixin, LearningLessonMixin, LearningSubmissionMixin):
    def __init__(
        self,
        repo: LearningRepository,
        wallet_repo: WalletRepository,
        step_evaluator: LearningStepSubmissionEvaluatorProtocol | None = None,
    ) -> None:
        self._repo = repo
        self._wallet = wallet_repo
        self._step_evaluator = step_evaluator or LearningStepSubmissionEvaluator()

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

    async def _ensure_legacy_lessons(self) -> None:
        courses = list_courses()
        sort_order = 100
        for course in courses:
            for _, _, _, lesson, _ in self._ordered_lessons(course):
                await self._repo.ensure_legacy_lesson(
                    slug=lesson["slug"],
                    title=pick_text(lesson["title"], "en"),
                    body=pick_text(lesson["summary"], "en"),
                    sort_order=sort_order,
                )
                sort_order += 1

    def _new_course_progress(self, *, user_id: uuid.UUID, course_slug: str, total_lessons: int) -> LearningCourseProgress:
        return LearningCourseProgress(
            user_id=user_id,
            course_slug=course_slug,
            status="active",
            total_lessons=total_lessons,
            completed_lessons=0,
            progress_percent=0,
            started_at=datetime.now(timezone.utc),
        )

    async def _ensure_course_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        total_lessons: int,
    ) -> LearningCourseProgress:
        row = await self._repo.get_course_progress(user_id, course_slug)
        if row is not None:
            return row
        return await self._repo.create_course_progress(
            self._new_course_progress(user_id=user_id, course_slug=course_slug, total_lessons=total_lessons)
        )

    async def _ensure_step_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        module_slug: str,
        lesson_slug: str,
        step_slug: str,
        step_kind: str,
    ) -> LearningStepProgress:
        row = await self._repo.get_step_progress(
            user_id=user_id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            step_slug=step_slug,
        )
        if row is not None:
            return row
        return await self._repo.create_step_progress(
            LearningStepProgress(
                user_id=user_id,
                course_slug=course_slug,
                module_slug=module_slug,
                lesson_slug=lesson_slug,
                step_slug=step_slug,
                step_kind=step_kind,
                status="not_started",
            )
        )

    async def _ensure_lesson_progress(
        self,
        *,
        user_id: uuid.UUID,
        course_slug: str,
        module_slug: str,
        lesson_slug: str,
        total_steps: int,
    ) -> LearningLessonProgress:
        row = await self._repo.get_lesson_progress(
            user_id=user_id,
            course_slug=course_slug,
            lesson_slug=lesson_slug,
        )
        if row is not None:
            return row
        return await self._repo.create_lesson_progress(
            LearningLessonProgress(
                user_id=user_id,
                course_slug=course_slug,
                module_slug=module_slug,
                lesson_slug=lesson_slug,
                total_steps=total_steps,
                status="in_progress",
            )
        )

