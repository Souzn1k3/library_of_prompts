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
        questions = [item for item in submission.get("questions", []) if isinstance(item, dict)]
        if questions:
            selected_map_raw = (answer or {}).get("choice_ids")
            if isinstance(selected_map_raw, dict):
                selected_map = {
                    str(question_id).lower(): str(choice_id).strip().lower()
                    for question_id, choice_id in selected_map_raw.items()
                    if isinstance(choice_id, str)
                }
            else:
                selected_map = {}
                selected = str((answer or {}).get("choice_id") or "").strip().lower()
                if selected:
                    selected_map["core"] = selected

            pass_score = int(submission.get("pass_score", 80))
            total_questions = len(questions)
            correct_count = 0
            improvements: list[str] = []
            answered_count = 0

            for index, question in enumerate(questions, start=1):
                question_id = str(question.get("id") or f"q{index}").lower()
                selected = selected_map.get(question_id, "")
                if selected:
                    answered_count += 1
                correct_ids = {str(item).lower() for item in question.get("correct_choices", [])}
                choice_map = {str(item["id"]).lower(): item for item in question.get("choices", [])}

                if selected in correct_ids and selected != "":
                    correct_count += 1
                    continue

                selected_expl = None
                if selected and selected in choice_map:
                    selected_expl = choice_map[selected].get("explanation")
                correct_expl = None
                for cid in correct_ids:
                    if cid in choice_map:
                        correct_expl = choice_map[cid].get("explanation")
                        break

                prefix = {
                    "en": f"Question {index}: ",
                    "ru": f"Вопрос {index}: ",
                    "tt": f"Сорау {index}: ",
                }[language]
                if isinstance(selected_expl, dict):
                    improvements.append(prefix + pick_text(selected_expl, language))
                elif isinstance(correct_expl, dict):
                    improvements.append(
                        prefix
                        + {
                            "en": "Review the stronger principle here: ",
                            "ru": "Здесь важно удержать более сильный принцип: ",
                            "tt": "Монда көчлерәк принципны истә тотарга кирәк: ",
                        }[language]
                        + pick_text(correct_expl, language)
                    )
                else:
                    improvements.append(prefix + self._feedback_message(language=language, key="wrong_choice"))

            score = round((correct_count / max(total_questions, 1)) * 100)
            passed = answered_count == total_questions and score >= pass_score
            strengths = [
                {
                    "en": f"Correct answers: {correct_count}/{total_questions}.",
                    "ru": f"Верных ответов: {correct_count}/{total_questions}.",
                    "tt": f"Дөрес җаваплар: {correct_count}/{total_questions}.",
                }[language]
            ]
            if passed:
                strengths.append(
                    {
                        "en": "You held the right decision rule across the whole quiz.",
                        "ru": "Вы удержали правильную логику выбора по всему квизу.",
                        "tt": "Сез бөтен квиз буенча дөрес сайлау логикасын сакладыгыз.",
                    }[language]
                )
            elif answered_count < total_questions:
                improvements.insert(
                    0,
                    {
                        "en": "Answer every quiz question before submitting.",
                        "ru": "Ответьте на все вопросы квиза перед отправкой.",
                        "tt": "Җибәргәнче квизның барлык сорауларына җавап бирегез.",
                    }[language]
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
                        "en": "Revisit the lesson theory and compare why the stronger option gives you more control.",
                        "ru": "Вернитесь к теории урока и еще раз сравните, почему сильный вариант дает больше контроля.",
                        "tt": "Дәрес теориясенә кире кайтыгыз һәм көчлерәк вариант нигә күбрәк контроль бирүен яңадан чагыштырыгыз.",
                    }[language]
                ],
                hint=(
                    {
                        "en": "Do not guess by tone. Look for explicit control over task, constraints, evidence, or evaluation.",
                        "ru": "Не гадайте по тону. Ищите явный контроль над задачей, ограничениями, evidence или оценкой.",
                        "tt": "Тон буенча фаразламагыз. Бурыч, чикләү, evidence яки бәяләү өстеннән ачык контроль эзләгез.",
                    }[language]
                ),
            )
            return passed, score, feedback

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
