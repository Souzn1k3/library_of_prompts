from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

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


def merge_localized_text(*values: Mapping[str, str]) -> LocalizedText:
    merged: LocalizedText = {language: "" for language in SUPPORTED_LEARNING_LANGUAGES}
    for language in SUPPORTED_LEARNING_LANGUAGES:
        parts: list[str] = []
        for value in values:
            candidate = str(value.get(language) or value.get("en") or "").strip()
            if candidate:
                parts.append(candidate)
        merged[language] = " ".join(parts).strip()
    return merged


def build_marker_template(markers: Iterable[str]) -> LocalizedText:
    scaffold = "\n".join(f"{marker.strip()} ..." for marker in markers if str(marker).strip())
    return {"en": scaffold, "ru": scaffold, "tt": scaffold}


def build_choice_question(
    *,
    question_id: str,
    question: LocalizedText,
    choices: list[dict[str, Any]],
    correct_choices: list[str],
) -> dict[str, Any]:
    return {
        "id": question_id,
        "question": question,
        "choices": choices,
        "correct_choices": correct_choices,
    }


_QUIZ_REASON_PREFIXES: dict[SupportedLearningLanguage, tuple[str, ...]] = {
    "en": ("Correct:",),
    "ru": ("Верно:",),
    "tt": ("Дөрес:",),
}


def _localized_value(value: LocalizedText, language: SupportedLearningLanguage) -> str:
    return str(value.get(language) or value.get("en") or "").strip()


def _clean_reason(value: LocalizedText, language: SupportedLearningLanguage) -> str:
    text = _localized_value(value, language)
    for prefix in _QUIZ_REASON_PREFIXES.get(language, ()):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    text = text.rstrip(".!? ").strip()
    if text:
        text = text[0].lower() + text[1:]
    return text


def _map_localized_text(
    callback: Callable[[SupportedLearningLanguage], str],
) -> LocalizedText:
    return {language: callback(language).strip() for language in SUPPORTED_LEARNING_LANGUAGES}


def build_five_question_quiz(
    *,
    question: LocalizedText,
    a: LocalizedText,
    b: LocalizedText,
    c: LocalizedText,
    exp_a: LocalizedText,
    exp_b: LocalizedText,
    exp_c: LocalizedText,
    pass_score: int = 80,
) -> dict[str, Any]:
    base_choices = [
        {"id": "a", "text": a, "explanation": exp_a},
        {"id": "b", "text": b, "explanation": exp_b},
        {"id": "c", "text": c, "explanation": exp_c},
    ]
    why_best_choices = [
        {
            "id": "a",
            "text": tr(
                "Because a loose request lets the model invent the missing details on its own.",
                "Потому что расплывчатый запрос якобы помогает модели самой додумать недостающие детали.",
                "Чөнки томан сорау модельгә җитмәгән детальләрне үзе уйлап табарга ярдәм итә имеш.",
            ),
        },
        {
            "id": "b",
            "text": _map_localized_text(
                lambda language: (
                    f"It wins because {_clean_reason(exp_b, language)}."
                    if language == "en"
                    else f"Он выигрывает, потому что {_clean_reason(exp_b, language)}."
                    if language == "ru"
                    else f"Ул җиңә, чөнки {_clean_reason(exp_b, language)}."
                )
            ),
        },
        {
            "id": "c",
            "text": tr(
                "Because the best option is simply the one that sounds longer and more confident.",
                "Потому что лучший вариант якобы всегда тот, который просто длиннее и звучит увереннее.",
                "Чөнки иң яхшысы имеш һәрвакыт озынрак һәм ышанычлырак яңгыраганы.",
            ),
        },
    ]
    repair_a_choices = [
        {
            "id": "a",
            "text": _map_localized_text(
                lambda language: (
                    f"Rewrite A around the working structure from the strong option: {_localized_value(b, language)}"
                    if language == "en"
                    else f"Пересобрать A вокруг рабочей опоры из сильного варианта: {_localized_value(b, language)}"
                    if language == "ru"
                    else f"A вариантын көчле варианттагы эш таянычы нигезендә яңадан җыярга: {_localized_value(b, language)}"
                )
            ),
        },
        {
            "id": "b",
            "text": tr(
                "Keep A just as vague, but make it look more serious and longer.",
                "Оставить A таким же расплывчатым, но сделать формулировку длиннее и солиднее.",
                "A ны шул ук томан хәлдә калдырып, бары тик озынрак һәм җитдирәк яңгыратырга.",
            ),
        },
        {
            "id": "c",
            "text": tr(
                "Leave A as-is and hope the next message can fix everything later.",
                "Оставить A как есть и надеяться, что все удастся исправить уже следующим сообщением.",
                "A ны үзгәртмичә калдырып, барысын да киләсе хәбәрдә төзәтеп булыр дип өметләнергә.",
            ),
        },
    ]
    risk_c_choices = [
        {
            "id": "a",
            "text": tr(
                "There is almost no risk left: option C is already specific enough to run.",
                "Серьезного риска почти нет: вариант C уже достаточно конкретный для работы.",
                "Җитди риск калмаган диярлек: C варианты эшләтерлек дәрәҗәдә инде җитәрлек төгәл.",
            ),
        },
        {
            "id": "b",
            "text": tr(
                "The main issue is only that option C sounds less clever than the others.",
                "Главная проблема якобы только в том, что вариант C звучит менее умно, чем остальные.",
                "Төп проблема имеш бары тик C вариантының башкаларга караганда акыллырак яңгырамавында гына.",
            ),
        },
        {
            "id": "c",
            "text": _map_localized_text(
                lambda language: (
                    f"Option C still stays weak because {_clean_reason(exp_c, language)}."
                    if language == "en"
                    else f"Вариант C все еще слабый, потому что {_clean_reason(exp_c, language)}."
                    if language == "ru"
                    else f"C варианты әле дә көчсез, чөнки {_clean_reason(exp_c, language)}."
                )
            ),
        },
    ]
    transfer_choices = [
        {
            "id": "a",
            "text": tr(
                "Start from the broadest wording and add structure only after the first weak answer.",
                "Начать с максимально общей формулировки и добавлять структуру только после первого слабого ответа.",
                "Иң гомуми формулировкадан башлап, структураны бары тик беренче зәгыйфь җаваптан соң гына өстәргә.",
            ),
        },
        {
            "id": "b",
            "text": _map_localized_text(
                lambda language: (
                    f"Carry the same principle into the next task: {_localized_value(b, language)}"
                    if language == "en"
                    else f"Перенести тот же принцип в следующую задачу: {_localized_value(b, language)}"
                    if language == "ru"
                    else f"Шул ук принципны киләсе бурычка күчерергә: {_localized_value(b, language)}"
                )
            ),
        },
        {
            "id": "c",
            "text": tr(
                "Choose the answer that sounds smartest, even when success is hard to verify.",
                "Выбирать ответ, который звучит умнее, даже если результат потом трудно проверить.",
                "Нәтиҗәне тикшерү авыр булса да, иң акыллырак яңгыраган җавапны сайларга.",
            ),
        },
    ]

    questions = [
        build_choice_question(
            question_id="core",
            question=question,
            choices=base_choices,
            correct_choices=["b"],
        ),
        build_choice_question(
            question_id="why_best",
            question=tr(
                "Why does the strong option beat the other two?",
                "Почему сильный вариант реально выигрывает у двух остальных?",
                "Ни өчен көчле вариант калган икесеннән чынлап та өстен чыга?",
            ),
            choices=why_best_choices,
            correct_choices=["b"],
        ),
        build_choice_question(
            question_id="trap_a",
            question=tr(
                "What is the best first fix for option A?",
                "Какая первая правка лучше всего лечит вариант A?",
                "A варианты өчен иң дөрес беренче төзәтмә кайсы?",
            ),
            choices=repair_a_choices,
            correct_choices=["a"],
        ),
        build_choice_question(
            question_id="trap_c",
            question=tr(
                "What risk stays alive in option C?",
                "Какой риск все еще живет внутри варианта C?",
                "C варианты эчендә нинди риск әле дә саклана?",
            ),
            choices=risk_c_choices,
            correct_choices=["c"],
        ),
        build_choice_question(
            question_id="transfer",
            question=tr(
                "Which next move shows that you understood the lesson, not just guessed the answer?",
                "Какой следующий ход показывает, что вы поняли урок, а не просто угадали ответ?",
                "Кайсы киләсе адым сезнең дәресне аңлаганыгызны, ә җавапны гына чамаламауыгызны күрсәтә?",
            ),
            choices=transfer_choices,
            correct_choices=["b"],
        ),
    ]

    return {
        "type": "choice",
        "pass_score": pass_score,
        "question": question,
        "choices": base_choices,
        "correct_choices": ["b"],
        "questions": questions,
    }


def strengthen_practice_steps(
    course: dict[str, Any],
    *,
    guided_suffix: LocalizedText,
    applied_suffix: LocalizedText,
    reflection_suffix: LocalizedText,
    reflection_template: LocalizedText,
) -> None:
    suffix_by_kind = {
        "guided_practice": guided_suffix,
        "applied_exercise": applied_suffix,
        "reflection": reflection_suffix,
    }

    for module in course.get("modules", []):
        for lesson in module.get("lessons", []):
            for step in lesson.get("steps", []):
                kind = str(step.get("kind") or "")
                suffix = suffix_by_kind.get(kind)
                task = step.get("task")
                if suffix and isinstance(task, Mapping):
                    step["task"] = merge_localized_text(task, suffix)

                submission = step.get("submission")
                required_markers = []
                if isinstance(submission, Mapping):
                    required_markers = [
                        str(marker).strip()
                        for marker in submission.get("required_markers", [])
                        if str(marker).strip()
                    ]

                if kind in {"guided_practice", "applied_exercise"} and not step.get("placeholder") and required_markers:
                    step["placeholder"] = build_marker_template(required_markers)

                if kind == "reflection" and not step.get("placeholder"):
                    step["placeholder"] = reflection_template


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


def pick_action(
    value: Mapping[str, Any] | None,
    language: SupportedLearningLanguage,
) -> dict[str, str | None] | None:
    if not isinstance(value, Mapping):
        return None

    href = str(value.get("href") or "").strip()
    label = value.get("label")
    if not href or not isinstance(label, Mapping):
        return None

    body = value.get("body")
    return {
        "label": pick_text(label, language),
        "href": href,
        "body": pick_text(body, language) if isinstance(body, Mapping) else None,
    }
