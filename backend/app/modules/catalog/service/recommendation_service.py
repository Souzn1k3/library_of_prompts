from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import Prompt, User
from app.modules.catalog.model.prompt import DiscoverySections, PromptListItem
from app.modules.catalog.model.recommendation import (
    PromptRecommendationResponse,
    RecommendationContext,
)
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.prompt_service import _to_list_item
from app.modules.catalog.service.recommendation_candidate_mixin import RecommendationCandidateMixin
from app.modules.catalog.service.recommendation_constants import UserSignalProfile
from app.modules.catalog.service.recommendation_profile_mixin import RecommendationProfileMixin
from app.modules.catalog.service.recommendation_scoring_mixin import RecommendationScoringMixin
from app.modules.catalog.service.recommendation_signal_mixin import RecommendationSignalMixin
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository


class RecommendationService(
    RecommendationSignalMixin,
    RecommendationProfileMixin,
    RecommendationCandidateMixin,
    RecommendationScoringMixin,
):
    def __init__(
        self,
        prompts: PromptRepository,
        saved_prompts: SavedPromptRepository,
        analytics: AnalyticsRepository,
        onboarding: OnboardingRepository,
        lessons: LessonRepository,
        missions: MissionRepository,
    ) -> None:
        self._prompts = prompts
        self._saved_prompts = saved_prompts
        self._analytics = analytics
        self._onboarding = onboarding
        self._lessons = lessons
        self._missions = missions

    async def discovery_sections(self, viewer: User | None, *, limit: int = 8) -> DiscoverySections:
        restrict = not can_view_restricted_category(viewer)
        recommendations = await self.recommend(
            viewer,
            context=RecommendationContext.home,
            limit=limit,
        )
        trending = await self._prompts.list_trending(limit=limit, restrict_to_unrestricted_categories=restrict)
        beginner = await self._prompts.list_best_for_beginners(
            limit=limit,
            restrict_to_unrestricted_categories=restrict,
        )
        most_saved = await self._prompts.list_most_saved(
            limit=limit,
            restrict_to_unrestricted_categories=restrict,
        )
        return DiscoverySections(
            for_you=recommendations.items,
            trending=[
                _to_list_item(row).model_copy(update={"recommendation_reason_key": "recommendation.reason.trending"})
                for row in trending
            ],
            best_for_beginners=[
                _to_list_item(row).model_copy(update={"recommendation_reason_key": "recommendation.reason.level"})
                for row in beginner
            ],
            most_saved=[
                _to_list_item(row).model_copy(update={"recommendation_reason_key": "recommendation.reason.curated"})
                for row in most_saved
            ],
        )

    async def related_prompts(
        self,
        slug: str,
        viewer: User | None,
        *,
        limit: int = 6,
    ) -> list[PromptListItem]:
        response = await self.recommend(
            viewer,
            context=RecommendationContext.prompt_detail,
            limit=limit,
            prompt_slug=slug,
        )
        return response.items

    async def recommend(
        self,
        viewer: User | None,
        *,
        context: RecommendationContext,
        limit: int = 6,
        prompt_slug: str | None = None,
        lesson_slug: str | None = None,
    ) -> PromptRecommendationResponse:
        profile: UserSignalProfile = await self._build_user_profile(viewer)
        restrict = not can_view_restricted_category(viewer)
        only_free = self._should_only_show_free(viewer, context)

        seed_prompt: Prompt | None = None
        if prompt_slug:
            seed_prompt = await self._prompts.get_by_slug(prompt_slug)
            if seed_prompt is None:
                raise NotFoundError("prompt", prompt_slug)
            if seed_prompt.category and seed_prompt.category.is_restricted and restrict:
                raise NotFoundError("prompt", prompt_slug)

        seed_lesson = None
        if lesson_slug:
            seed_lesson = await self._lessons.get_by_slug(lesson_slug)
            if seed_lesson is None:
                raise NotFoundError("lesson", lesson_slug)

        candidates = await self._candidate_pool(
            viewer,
            profile,
            context=context,
            limit=limit,
            seed_prompt=seed_prompt,
            seed_lesson=seed_lesson,
            restrict_to_unrestricted_categories=restrict,
            only_free=only_free,
        )
        selected = self._select_diverse_candidates(
            candidates,
            profile=profile,
            context=context,
            seed_prompt=seed_prompt,
            seed_lesson=seed_lesson,
            limit=limit,
        )

        return PromptRecommendationResponse(
            context=context,
            strategy=self._recommendation_strategy(context, profile),
            items=selected,
        )
