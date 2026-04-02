from __future__ import annotations

from collections.abc import Mapping

SupportedLearningLanguage = str
SUPPORTED_LEARNING_LANGUAGES: tuple[SupportedLearningLanguage, ...] = ("en", "ru", "tt")

LocalizedText = dict[SupportedLearningLanguage, str]


def tr(en: str, ru: str, tt: str) -> LocalizedText:
    return {"en": en, "ru": ru, "tt": tt}


def pick_text(value: LocalizedText | Mapping[str, str], language: SupportedLearningLanguage) -> str:
    if language in value and value[language]:
        return str(value[language])
    if "en" in value and value["en"]:
        return str(value["en"])
    return str(next(iter(value.values()), ""))
