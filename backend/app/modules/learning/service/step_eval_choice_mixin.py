from __future__ import annotations

from typing import Any

from app.core.i18n import SupportedLanguage
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import LearningStepFeedbackRead


class LearningStepChoiceEvaluationMixin:
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
            verdict={
                True: {"en": "Correct", "ru": "Верно", "tt": "Дөрес"},
                False: {"en": "Incorrect", "ru": "Неверно", "tt": "Дөрес түгел"},
            }[passed][language],
            score=score,
            pass_score=pass_score,
            strengths=strengths,
            improvements=improvements,
            revisit=[]
            if passed
            else [
                {
                    "en": "Revisit the lesson micro-theory before retry.",
                    "ru": "Перед повтором вернитесь к микро-теории урока.",
                    "tt": "Кабатлаганчы дәреснең микро-теориясен яңадан карагыз.",
                }[language]
            ],
            hint=None,
        )
        return passed, score, feedback
