import uuid

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_optional_user
from app.api.service_deps import (
    get_prompt_engagement_service,
    get_prompt_service,
    get_recommendation_service,
)
from app.api.v1.routers.prompt_cache_keys import (
    allow_auto_plan_unlock,
    discovery_sections_suffix,
    normalize_multi_filter,
    prompt_list_suffix,
    recommendation_suffix,
    related_suffix,
)
from app.core.cache import get_cache
from app.infrastructure.db.models import PromptDifficulty, PromptOutputType, PromptTechnique, User
from app.modules.economy.model.store import EconomyActionRead
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
from app.modules.catalog.service.prompt_engagement_service import PromptEngagementService

router = APIRouter(prefix="/prompts", tags=["prompts"])
_PROMPT_CACHE_TTL = 75
_DISCOVERY_CACHE_TTL = 90


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
        suffix=discovery_sections_suffix(viewer=viewer, limit=limit),
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
    normalized_use_case = normalize_multi_filter(use_case)
    normalized_models = normalize_multi_filter(model)
    normalized_tags = normalize_multi_filter(tag)
    cache = get_cache()

    suffix = prompt_list_suffix(
        skip=skip,
        limit=limit,
        q=q,
        contributor=contributor,
        category_id=category_id,
        technique=technique,
        difficulty=difficulty,
        output_type=output_type,
        use_cases=normalized_use_case,
        model_compatibility=normalized_models,
        tags=normalized_tags,
        sort=sort,
        viewer=viewer,
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
        suffix=related_suffix(viewer=viewer, slug=slug, limit=limit),
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
        suffix=recommendation_suffix(
            viewer=viewer,
            context=context,
            limit=limit,
            prompt_slug=prompt_slug,
            lesson_slug=lesson_slug,
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


@router.post("/{prompt_id}/events/copy", response_model=EconomyActionRead)
async def track_copy(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    engagement: PromptEngagementService = Depends(get_prompt_engagement_service),
) -> EconomyActionRead:
    return await engagement.track_copy(
        prompt_id=prompt_id,
        viewer=viewer,
    )


@router.post("/{prompt_id}/events/apply", response_model=EconomyActionRead)
async def track_apply(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    engagement: PromptEngagementService = Depends(get_prompt_engagement_service),
) -> EconomyActionRead:
    return await engagement.track_apply(
        prompt_id=prompt_id,
        viewer=viewer,
    )


@router.get("/by-slug/{slug}", response_model=PromptRead)
async def get_prompt_by_slug(
    request: Request,
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
) -> PromptRead:
    return await svc.get_by_slug(
        slug,
        viewer,
        auto_grant_included_unlock=allow_auto_plan_unlock(request),
    )


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    request: Request,
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(get_prompt_service),
) -> PromptRead:
    return await svc.get_by_id(
        prompt_id,
        viewer,
        auto_grant_included_unlock=allow_auto_plan_unlock(request),
    )
