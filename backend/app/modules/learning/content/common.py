from __future__ import annotations

from collections.abc import Iterable, Mapping

SupportedLearningLanguage = str
SUPPORTED_LEARNING_LANGUAGES: tuple[SupportedLearningLanguage, ...] = ("en", "ru", "tt")

LocalizedText = dict[SupportedLearningLanguage, str]

_LOCALIZED_TERM_REPLACEMENTS: dict[SupportedLearningLanguage, tuple[tuple[str, str], ...]] = {
    "en": (),
    "ru": (
        ("prompt-workflow", "промпт-процесс"),
        ("research-workflow", "исследовательский процесс"),
        ("writing-workflow", "процесс написания текста"),
        ("debug+fix workflow", "процесс диагностики и исправления"),
        ("decision-промпт", "промпт для принятия решения"),
        ("debug-промпт", "диагностический промпт"),
        ("debug+fix", "диагностика+исправление"),
        ("Version A + Version B", "Версия A + Версия B"),
        ("deployment note", "заметку по внедрению"),
        ("end-to-end", "сквозной"),
        ("Role-Context-Task-Output", "Роль-Контекст-Задача-Формат ответа"),
        ("Actionability", "Практическая применимость"),
        ("Prompt v1", "Промпт v1"),
        ("Prompt v2", "Промпт v2"),
        ("Role", "Роль"),
        ("context", "контекст"),
        ("task", "задача"),
        ("output", "формат ответа"),
        ("fallback", "резервный"),
        ("capstone", "финальный проект"),
        ("workflows", "рабочие процессы"),
        ("Workflow", "Рабочий процесс"),
        ("workflow", "рабочий процесс"),
        ("deliverable", "итоговый результат"),
        ("planner -> writer -> editor", "планировщик -> автор -> редактор"),
        ("score", "оценка"),
    ),
    "tt": (
        ("prompt-workflow", "промпт-эш агымы"),
        ("research-workflow", "тикшеренү эш агымы"),
        ("writing-workflow", "язу эш агымы"),
        ("debug+fix workflow", "диагностика һәм төзәтү эш агымы"),
        ("decision-промпт", "карар промпты"),
        ("debug-промпт", "диагностика промпты"),
        ("debug+fix", "диагностика+төзәтү"),
        ("Version A + Version B", "Версия A + Версия B"),
        ("deployment note", "кертү искәрмәсе"),
        ("end-to-end", "тулысынча"),
        ("Role-Context-Task-Output", "Роль-Контекст-Бурыч-Җавап форматы"),
        ("Actionability", "кулланышлылык"),
        ("Prompt v1", "Промпт v1"),
        ("Prompt v2", "Промпт v2"),
        ("Role", "Роль"),
        ("context", "контекст"),
        ("task", "бурыч"),
        ("output", "җавап форматы"),
        ("fallback", "резерв"),
        ("capstone", "финал проект"),
        ("workflows", "эш агымнары"),
        ("Workflow", "Эш агымы"),
        ("workflow", "эш агымы"),
        ("deliverable", "тапшырыла торган нәтиҗә"),
        ("planner -> writer -> editor", "планлаучы -> язучы -> редактор"),
        ("score", "бәя"),
    ),
}

_FORBIDDEN_PHRASE_GROUPS: tuple[dict[SupportedLearningLanguage, str], ...] = (
    {"en": "any format", "ru": "в любом формате", "tt": "теләсә нинди форматта"},
    {"en": "as you wish", "ru": "как хотите", "tt": "үзеңчә"},
    {"en": "whatever works", "ru": "как угодно", "tt": "ничек булса да ярый"},
    {"en": "just make it good", "ru": "сделай нормально", "tt": "нормаль итеп эшлә"},
)

_FORBIDDEN_PHRASE_LOOKUP: dict[str, dict[SupportedLearningLanguage, str]] = {}
for group in _FORBIDDEN_PHRASE_GROUPS:
    for phrase in group.values():
        _FORBIDDEN_PHRASE_LOOKUP[phrase.strip().lower()] = group


def tr(en: str, ru: str, tt: str) -> LocalizedText:
    return {"en": en, "ru": ru, "tt": tt}


def localize_learning_text(value: str, language: SupportedLearningLanguage) -> str:
    text = value
    for source, target in _LOCALIZED_TERM_REPLACEMENTS.get(language, ()):
        text = text.replace(source, target)
    return text


def localize_forbidden_phrases(values: Iterable[str], language: SupportedLearningLanguage) -> list[str]:
    localized: list[str] = []
    seen: set[str] = set()
    for phrase in values:
        normalized_key = phrase.strip().lower()
        group = _FORBIDDEN_PHRASE_LOOKUP.get(normalized_key)
        item = group.get(language, phrase) if group else localize_learning_text(phrase, language)
        dedupe_key = item.strip().lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        localized.append(item)
    return localized


def pick_text(value: LocalizedText | Mapping[str, str], language: SupportedLearningLanguage) -> str:
    if language in value and value[language]:
        return localize_learning_text(str(value[language]), language)
    if "en" in value and value["en"]:
        return localize_learning_text(str(value["en"]), language)
    return localize_learning_text(str(next(iter(value.values()), "")), language)
