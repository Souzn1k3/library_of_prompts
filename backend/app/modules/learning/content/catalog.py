from __future__ import annotations

from copy import deepcopy

from app.modules.learning.content.course_enrichment import apply_course_enrichment
from app.modules.learning.content.prompt_basics import PROMPT_BASICS_COURSE
from app.modules.learning.content.production_systems import PRODUCTION_SYSTEMS_COURSE
from app.modules.learning.content.workflows import WORKFLOWS_COURSE

LEARNING_COURSES: list[dict] = [
    apply_course_enrichment(PROMPT_BASICS_COURSE),
    apply_course_enrichment(WORKFLOWS_COURSE),
    PRODUCTION_SYSTEMS_COURSE,
]

COURSE_BY_SLUG: dict[str, dict] = {course["slug"]: course for course in LEARNING_COURSES}

LESSON_INDEX_BY_SLUG: dict[str, tuple[str, str, dict]] = {}
for _course in LEARNING_COURSES:
    course_slug = _course["slug"]
    for _module in _course["modules"]:
        module_slug = _module["slug"]
        for _lesson in _module["lessons"]:
            lesson_slug = _lesson["slug"]
            LESSON_INDEX_BY_SLUG[lesson_slug] = (course_slug, module_slug, _lesson)


def list_courses() -> list[dict]:
    return deepcopy(LEARNING_COURSES)


def get_course(course_slug: str) -> dict | None:
    row = COURSE_BY_SLUG.get(course_slug)
    return deepcopy(row) if row is not None else None


def find_lesson(lesson_slug: str) -> tuple[str, str, dict] | None:
    row = LESSON_INDEX_BY_SLUG.get(lesson_slug)
    if row is None:
        return None
    course_slug, module_slug, lesson = row
    return course_slug, module_slug, deepcopy(lesson)

