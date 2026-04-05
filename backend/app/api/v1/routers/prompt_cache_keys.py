from __future__ import annotations

import uuid
from urllib.parse import quote_plus

from fastapi import Request

from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import PromptDifficulty, PromptOutputType, PromptTechnique, User
from app.modules.catalog.model.prompt import PromptSort
from app.modules.catalog.model.recommendation import RecommendationContext


def normalize_multi_filter(value: list[str] | None) -> list[str] | None:
    if not value:
        return None
    out: list[str] = []
    for item in value:
        chunks = [chunk.strip().lower() for chunk in item.split(",")]
        out.extend(chunk for chunk in chunks if chunk)
    return out or None


def viewer_segment(viewer: User | None) -> str:
    return str(viewer.id) if viewer is not None else "anon"


def catalog_visibility(viewer: User | None) -> str:
    return "all" if can_view_restricted_category(viewer) else "public"


def allow_auto_plan_unlock(request: Request) -> bool:
    # Prevent cross-site top-level navigations from consuming included unlock quota via GET.
    fetch_site = (request.headers.get("sec-fetch-site") or "").strip().lower()
    return fetch_site != "cross-site"


def discovery_sections_suffix(*, viewer: User | None, limit: int) -> str:
    return (
        f"discovery-sections:user={viewer_segment(viewer)}"
        f":visibility={catalog_visibility(viewer)}:limit={limit}"
    )


def related_suffix(*, viewer: User | None, slug: str, limit: int) -> str:
    return (
        f"related:user={viewer_segment(viewer)}:slug={_norm(slug)}:limit={limit}"
        f":visibility={catalog_visibility(viewer)}"
    )


def recommendation_suffix(
    *,
    viewer: User | None,
    context: RecommendationContext,
    limit: int,
    prompt_slug: str | None,
    lesson_slug: str | None,
) -> str:
    return (
        f"bundle:user={viewer_segment(viewer)}:context={context.value}:limit={limit}"
        f":prompt={_norm(prompt_slug)}:lesson={_norm(lesson_slug)}"
        f":visibility={catalog_visibility(viewer)}"
    )


def prompt_list_suffix(
    *,
    skip: int,
    limit: int,
    q: str | None,
    contributor: str | None,
    category_id: uuid.UUID | None,
    technique: PromptTechnique | None,
    difficulty: PromptDifficulty | None,
    output_type: PromptOutputType | None,
    use_cases: list[str] | None,
    model_compatibility: list[str] | None,
    tags: list[str] | None,
    sort: PromptSort,
    viewer: User | None,
) -> str:
    return (
        f"list:skip={skip}:limit={limit}"
        f":q={_norm(q)}:contributor={_norm(contributor)}"
        f":category={str(category_id) if category_id is not None else '-'}"
        f":technique={technique.value if technique is not None else '-'}"
        f":difficulty={difficulty.value if difficulty is not None else '-'}"
        f":output={output_type.value if output_type is not None else '-'}"
        f":use_case={_norm_multi(use_cases)}"
        f":model={_norm_multi(model_compatibility)}"
        f":tag={_norm_multi(tags)}"
        f":sort={sort.value}:visibility={catalog_visibility(viewer)}:user={viewer_segment(viewer)}"
    )


def _norm(value: str | None) -> str:
    if value is None:
        return "-"
    stripped = value.strip()
    if not stripped:
        return "-"
    return quote_plus(stripped.lower())


def _norm_multi(values: list[str] | None) -> str:
    if not values:
        return "-"
    normalized_tokens: set[str] = set()
    for value in values:
        token = _norm(value)
        if token != "-":
            normalized_tokens.add(token)
    normalized = sorted(normalized_tokens)
    return ",".join(normalized) if normalized else "-"
