from __future__ import annotations

from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import LearningLessonProgress, LearningStepProgress
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import (
    LearningLessonOutlineRead,
    LearningLessonStatus,
    LearningLessonStepRead,
    LearningStepChoiceRead,
    LearningStepFeedbackRead,
)


class LearningLessonProjectionMixin:
    def _build_lesson_steps(
        self,
        *,
        lesson: dict,
        step_progress_rows: list[LearningStepProgress],
        language: SupportedLanguage,
    ) -> tuple[list[LearningLessonStepRead], set[str]]:
        step_progress_map = {row.step_slug: row for row in step_progress_rows}
        completed_steps = {row.step_slug for row in step_progress_rows if row.passed}
        steps_out: list[LearningLessonStepRead] = []
        for step in lesson["steps"]:
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
        return steps_out, completed_steps

    def _build_lesson_outline(
        self,
        *,
        ordered_lessons: list[tuple[int, dict, int, dict, int]],
        lesson_progress_rows: list[LearningLessonProgress],
        language: SupportedLanguage,
        course_slug: str,
    ) -> list[LearningLessonOutlineRead]:
        lesson_progress_map = {row.lesson_slug: row for row in lesson_progress_rows}
        completed_lessons = {row.lesson_slug for row in lesson_progress_rows if row.status == "completed"}
        outline: list[LearningLessonOutlineRead] = []
        for _, _module, lesson_pos, lesson, _global_pos in ordered_lessons:
            row = lesson_progress_map.get(lesson["slug"])
            status: LearningLessonStatus = (
                "completed"
                if row is not None and row.status == "completed"
                else ("in_progress" if row is not None else "not_started")
            )
            outline.append(
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
        return outline
