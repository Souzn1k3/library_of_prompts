import uuid
from datetime import datetime, timezone
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_optional_user
from app.api.service_deps import (
    get_contributor_service,
    get_mission_service,
    get_prompt_service,
    get_recommendation_service,
)
from app.core.cache import get_cache
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import PromptDifficulty, PromptOutputType, PromptTechnique, User
from app.modules.catalog.model.prompt import (
    DiscoverySections,
    PromptDiscoveryFilters,
    PromptListItem,
    PromptRead,
    PromptSort,
)
from app.modules.catalog.model.recommendation import (
    PromptRecommendationResponse,
    RecommendationContext,
)
from app.modules.catalog.service.prompt_service import PromptService
from app.modules.catalog.service.recommendation_service import RecommendationService
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/prompts", tags=["prompts"])
_PROMPT_CACHE_TTL = 75
_DISCOVERY_CACHE_TTL = 90


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
    normalized = sorted({_norm(v) for v in values if _norm(v) != "-"})
    return ",".join(normalized) if normalized else "-"


def _catalog_visibility(viewer: User | None) -> str:
    return "all" if can_view_restricted_category(viewer) else "public"


def _normalize_multi(value: list[str] | None) -> list[str] | None:
    if not value:
        return None
    out: list[str] = []
    for item in value:
        chunks = [chunk.strip().lower() for chunk in item.split(",")]
        out.extend([chunk for chunk in chunks if chunk])
    return out or None


def _viewer_segment(viewer: User | None) -> str:
    return str(viewer.id) if viewer is not None else "anon"


@router.get("/discovery-filters", response_model=PromptDiscoveryFilters)
async def discovery_filters(
    svc: PromptService = Depends(get_prompt_service),
) -> PromptDiscoveryFilters:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="prompts",
        suffix="discovery-filters",
        loader=svc.discovery_filters,
        ttl_seconds=_DISCOVERY_CACHE_TTL,
    )


@router.get("/discovery-sections", response_model=DiscoverySections)
async def discovery_sections(
    limit: int = Query(default=8, ge=1, le=24),
    viewer: User | None = Depends(get_optional_user),
    svc: RecommendationService = Depends(get_recommendation_service),
) -> DiscoverySections:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="recommendations",
        suffix=f"discovery-sections:user={_viewer_segment(viewer)}:visibility={_catalog_visibility(viewer)}:limit={limit}",
        loader=lambda: svc.discovery_sections(viewer, limit=limit),
        ttl_seconds=_DISCOVERY_CACHE_TTL,
    )


@router.get("", response_model=list[PromptListItem])
async def list_prompts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=100),
    q: str | None = Query(default=None, description="Intent-aware search with FTS + fuzzy matching"),
    contributor: str | None = Query(default=None, description="Filter by contributor slug"),
    category_id: uuid.UUID | None = Query(default=None),
    technique: PromptTechnique | None = Query(default=None),
    difficulty: PromptDifficulty | None = Query(default=None),
    output_type: PromptOutputType | None = Query(default=None),
    use_case: list[str] | None = Query(default=None),
    model: list[str] | None = Query(default=None),
    tag: list[str] | None = Query(default=None),
    sort: PromptSort = Query(default=PromptSort.relevance),
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
) -> list[PromptListItem]:
    normalized_use_case = _normalize_multi(use_case)
    normalized_models = _normalize_multi(model)
    normalized_tags = _normalize_multi(tag)
    visibility = _catalog_visibility(viewer)
    cache = get_cache()

    suffix = (
        f"list:skip={skip}:limit={limit}"
        f":q={_norm(q)}:contributor={_norm(contributor)}"
        f":category={str(category_id) if category_id is not None else '-'}"
        f":technique={technique.value if technique is not None else '-'}"
        f":difficulty={difficulty.value if difficulty is not None else '-'}"
        f":output={output_type.value if output_type is not None else '-'}"
        f":use_case={_norm_multi(normalized_use_case)}"
        f":model={_norm_multi(normalized_models)}"
        f":tag={_norm_multi(normalized_tags)}"
        f":sort={sort.value}:visibility={visibility}"
    )

    return await cache.get_or_set_json(
        namespace="prompts",
        suffix=suffix,
        loader=lambda: svc.list_published(
            viewer,
            skip=skip,
            limit=limit,
            q=q,
            contributor_slug=contributor,
            category_id=category_id,
            technique=technique,
            difficulty=difficulty,
            output_type=output_type,
            use_cases=normalized_use_case,
            model_compatibility=normalized_models,
            tags=normalized_tags,
            sort=sort,
        ),
        ttl_seconds=_PROMPT_CACHE_TTL,
    )


@router.get("/by-slug/{slug}/related", response_model=list[PromptListItem])
async def related_prompts(
    slug: str,
    limit: int = Query(default=6, ge=1, le=24),
    viewer: User | None = Depends(get_optional_user),
    svc: RecommendationService = Depends(get_recommendation_service),
) -> list[PromptListItem]:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="recommendations",
        suffix=(
            f"related:user={_viewer_segment(viewer)}:slug={_norm(slug)}:limit={limit}"
            f":visibility={_catalog_visibility(viewer)}"
        ),
        loader=lambda: svc.related_prompts(slug, viewer, limit=limit),
        ttl_seconds=_PROMPT_CACHE_TTL,
    )


@router.get("/recommendations", response_model=PromptRecommendationResponse)
async def prompt_recommendations(
    context: RecommendationContext = Query(default=RecommendationContext.dashboard),
    limit: int = Query(default=6, ge=1, le=24),
    prompt_slug: str | None = Query(default=None),
    lesson_slug: str | None = Query(default=None),
    viewer: User | None = Depends(get_optional_user),
    svc: RecommendationService = Depends(get_recommendation_service),
) -> PromptRecommendationResponse:
    cache = get_cache()
    return await cache.get_or_set_json(
        namespace="recommendations",
        suffix=(
            f"bundle:user={_viewer_segment(viewer)}:context={context.value}:limit={limit}"
            f":prompt={_norm(prompt_slug)}:lesson={_norm(lesson_slug)}"
            f":visibility={_catalog_visibility(viewer)}"
        ),
        loader=lambda: svc.recommend(
            viewer,
            context=context,
            limit=limit,
            prompt_slug=prompt_slug,
            lesson_slug=lesson_slug,
        ),
        ttl_seconds=_PROMPT_CACHE_TTL,
    )


@router.post("/{prompt_id}/events/copy", status_code=204)
async def track_copy(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
    missions: MissionService = Depends(get_mission_service),
    contributors: ContributorService = Depends(get_contributor_service),
) -> Response:
    await svc.track_copy(prompt_id, viewer)
    if viewer is not None:
        today_key = datetime.now(timezone.utc).date().isoformat()
        await missions.record_event(
            user=viewer,
            event_type="prompt_copied",
            prompt_id=prompt_id,
        )
        await missions.record_event(
            user=viewer,
            event_type="streak_activity",
            prompt_id=prompt_id,
            source_event_key=f"streak_activity:{viewer.id}:{today_key}",
            payload={"source": "prompt_copied"},
        )
    await contributors.refresh_prompt_quality(prompt_id)
    await get_cache().bump_many(("prompts", "contributors", "recommendations"))
    return Response(status_code=204)


@router.post("/{prompt_id}/events/apply", status_code=204)
async def track_apply(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    missions: MissionService = Depends(get_mission_service),
) -> Response:
    if viewer is not None:
        today_key = datetime.now(timezone.utc).date().isoformat()
        await missions.record_event(
            user=viewer,
            event_type="prompt_applied",
            prompt_id=prompt_id,
            source_event_key=f"prompt_applied:{viewer.id}:{prompt_id}",
        )
        await missions.record_event(
            user=viewer,
            event_type="streak_activity",
            prompt_id=prompt_id,
            source_event_key=f"streak_activity:{viewer.id}:{today_key}",
            payload={"source": "prompt_applied"},
        )
    return Response(status_code=204)


@router.get("/by-slug/{slug}", response_model=PromptRead)
async def get_prompt_by_slug(
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
) -> PromptRead:
    return await svc.get_by_slug(slug, viewer)


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
) -> PromptRead:
    return await svc.get_by_id(prompt_id, viewer)
