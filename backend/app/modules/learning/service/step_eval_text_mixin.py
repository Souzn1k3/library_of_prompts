from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.core.i18n import SupportedLanguage
from app.modules.learning.model.learning import LearningStepFeedbackRead
from app.modules.learning.service.step_eval_helpers import (
    extract_marker_payload,
    normalize_text,
    tokenize,
    word_count,
)


class LearningStepTextEvaluationMixin:
    def _validate_text_submission(
        self,
        *,
        submission: dict[str, Any],
        answer: dict[str, Any] | None,
        language: SupportedLanguage,
    ) -> tuple[bool, int, LearningStepFeedbackRead]:
        text = str((answer or {}).get("text") or "").strip()
        normalized = normalize_text(text)
        min_words = int(submission.get("min_words", 1))
        required_markers = [str(marker) for marker in submission.get("required_markers", [])]
        bonus_markers = [str(marker) for marker in submission.get("bonus_markers", [])]
        forbidden = [str(marker) for marker in submission.get("forbidden_phrases", [])]
        pass_score = int(submission.get("pass_score", 70))

        wc = word_count(text)
        missing_markers = [marker for marker in required_markers if marker.lower() not in normalized]
        bonus_hits = [marker for marker in bonus_markers if marker.lower() in normalized]
        forbidden_hits = [marker for marker in forbidden if marker.lower() in normalized]
        marker_payload_words: dict[str, int] = {}
        for marker in required_markers:
            payload = extract_marker_payload(text, marker)
            marker_payload_words[marker] = word_count(payload)
        empty_markers = [
            marker
            for marker, count in marker_payload_words.items()
            if marker not in missing_markers and count < 3
        ]

        tokens = tokenize(text)
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
