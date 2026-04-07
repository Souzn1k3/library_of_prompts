from __future__ import annotations

from app.core.i18n import SupportedLanguage
from app.infrastructure.db.models import LearningLessonProgress, LearningStepProgress
from app.modules.learning.content.common import localize_forbidden_phrases, pick_text
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
        can_unlock_next_step = True
        for step in lesson["steps"]:
            submission = step.get("submission", {"type": "none"})
            submission_type = submission.get("type", "none")
            pass_score = 100 if submission_type == "none" else int(submission.get("pass_score", 0))
            row = step_progress_map.get(step["slug"])
            feedback = None
            if row is not None and isinstance(row.feedback_json, dict):
                feedback = LearningStepFeedbackRead.model_validate(row.feedback_json)
            last_answer_text = None
            last_choice_id = None
            if row is not None and isinstance(row.answer_json, dict):
                raw_text = row.answer_json.get("text")
                raw_choice = row.answer_json.get("choice_id")
                if isinstance(raw_text, str):
                    last_answer_text = raw_text
                if isinstance(raw_choice, str):
                    last_choice_id = raw_choice
            completed = bool(row.passed) if row is not None else False
            unlocked = can_unlock_next_step or completed

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
                        LearningStepChoiceRead(
                            id=choice["id"],
                            text=pick_text(choice["text"], language),
                            explanation=pick_text(choice["explanation"], language) if choice.get("explanation") else None,
                        )
                        for choice in submission.get("choices", [])
                    ],
                    pass_score=pass_score,
                    min_words=int(submission["min_words"]) if submission.get("min_words") is not None else None,
                    required_markers=[str(marker) for marker in submission.get("required_markers", [])],
                    bonus_markers=[str(marker) for marker in submission.get("bonus_markers", [])],
                    forbidden_phrases=localize_forbidden_phrases(
                        [str(marker) for marker in submission.get("forbidden_phrases", [])],
                        language,
                    ),
                    submission_type=submission_type,
                    unlocked=unlocked,
                    completed=completed,
                    attempts=int(row.attempts) if row is not None else 0,
                    last_score=int(row.last_score) if row is not None else None,
                    last_answer_text=last_answer_text,
                    last_choice_id=last_choice_id,
                    feedback=feedback,
                )
            )
            if not completed:
                can_unlock_next_step = False
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
        lesson_unlock_map = self._lesson_unlock_map(
            ordered_lessons=ordered_lessons,
            completed_lessons=completed_lessons,
        )
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
                    unlocked=lesson_unlock_map.get(lesson["slug"], False),
                    is_final_assessment=bool(lesson.get("is_final_assessment", False)),
                    progress_percent=int(row.progress_percent) if row is not None else 0,
                    continue_href=f"/learn/course/{course_slug}/lesson/{lesson['slug']}",
                )
            )
        return outline
