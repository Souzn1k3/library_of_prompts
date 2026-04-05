from __future__ import annotations

from typing import Any, Protocol

from app.core.i18n import SupportedLanguage
from app.modules.learning.model.learning import LearningStepFeedbackRead
from app.modules.learning.service.step_eval_choice_mixin import LearningStepChoiceEvaluationMixin
from app.modules.learning.service.step_eval_text_mixin import LearningStepTextEvaluationMixin


class LearningStepSubmissionEvaluatorProtocol(Protocol):
    def evaluate(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]: ...


class LearningStepSubmissionEvaluator(LearningStepTextEvaluationMixin, LearningStepChoiceEvaluationMixin):
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

    def evaluate(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]:
        submission_type = submission.get("type", "none")
        if submission_type == "none":
            return (
                True,
                100,
                LearningStepFeedbackRead(
                    verdict={"en": "Completed", "ru": "Завершено", "tt": "Тәмам"}[language],
                    score=100,
                    pass_score=100,
                    strengths=[
                        {
                            "en": "Step marked as completed.",
                            "ru": "Шаг отмечен завершенным.",
                            "tt": "Адым тәмамланды дип билгеләнде.",
                        }[language]
                    ],
                    improvements=[],
                    revisit=[],
                    hint=None,
                ),
            )
        if submission_type == "choice":
            return self._validate_choice_submission(
                submission=submission,
                answer=answer,
                language=language,
            )
        return self._validate_text_submission(
            submission=submission,
            answer=answer,
            language=language,
        )
