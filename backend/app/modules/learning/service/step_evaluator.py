from __future__ import annotations

import re
from collections import Counter
from typing import Any, Protocol

from app.core.i18n import SupportedLanguage
from app.modules.learning.content.common import pick_text
from app.modules.learning.model.learning import LearningStepFeedbackRead


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


class LearningStepSubmissionEvaluatorProtocol(Protocol):
    def evaluate(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]: ...


class LearningStepSubmissionEvaluator:
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
        most_common_share = token_counter.most_common(1)[0][1] / len(tokens) if tokens else 0.0
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
