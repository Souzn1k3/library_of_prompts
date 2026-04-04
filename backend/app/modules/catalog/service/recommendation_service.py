from __future__ import annotations
import math
import re
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.core.errors import NotFoundError
from app.core.tiers import can_view_premium_content, can_view_restricted_category
from app.infrastructure.db.models import Prompt, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.catalog.model.prompt import DiscoverySections, PromptListItem, PromptSort
from app.modules.catalog.model.recommendation import (
    PromptRecommendationResponse,
    RecommendationContext,
    RecommendationStrategy,
)
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.prompt_service import _to_list_item
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository

_WORD_RE = re.compile(r"[\w-]{3,}", re.UNICODE)
_STOPWORDS = {
    "and",
    "are",
    "assistant",
    "chat",
    "for",
    "from",
    "into",
    "prompt",
    "prompts",
    "that",
    "the",
    "this",
    "with",
    "your",
}
_PROFILE_KEYWORDS: dict[str, list[str]] = {
    "student": ["study", "exam", "summary", "explain"],
    "developer": ["code", "debug", "api", "refactor"],
    "other": ["workflow", "planning", "research", "writing"],
    "learning": ["learn", "tutorial", "practice", "explain"],
    "solving_tasks": ["analysis", "solve", "task", "step"],
    "productivity": ["organize", "workflow", "checklist", "time"],
    "chatgpt": ["assistant", "chat"],
    "code_assistant": ["code", "debug", "test"],
    "school": ["study", "notes", "exam"],
    "work": ["email", "meeting", "planning"],
}
_ANALYTICS_WEIGHTS = {
    AnalyticsEventName.prompt_saved: 3.0,
    AnalyticsEventName.prompt_copied: 2.25,
    AnalyticsEventName.prompt_viewed: 0.9,
}
_CONTEXTUAL_STRATEGY_CONTEXTS = {
    RecommendationContext.prompt_detail,
    RecommendationContext.after_save,
    RecommendationContext.after_lesson_complete,
}
_BEGINNER_CANDIDATE_CONTEXTS = {
    RecommendationContext.dashboard,
    RecommendationContext.after_save,
    RecommendationContext.after_lesson_complete,
}
_CONTEXT_SCORE_WEIGHTS: dict[RecommendationContext, tuple[float, float, float, float, float]] = {
    RecommendationContext.prompt_detail: (0.58, 0.12, 0.08, 0.22, 0.0),
    RecommendationContext.after_save: (0.42, 0.28, 0.1, 0.2, 0.0),
    RecommendationContext.after_lesson_complete: (0.44, 0.22, 0.1, 0.24, 0.0),
    RecommendationContext.dashboard: (0.0, 0.44, 0.14, 0.26, 0.16),
    RecommendationContext.home: (0.0, 0.34, 0.16, 0.34, 0.16),
}


@dataclass
class UserSignalProfile:
    saved_prompt_ids: set[uuid.UUID] = field(default_factory=set)
    recent_prompt_ids: list[uuid.UUID] = field(default_factory=list)
    category_weights: dict[uuid.UUID, float] = field(default_factory=lambda: defaultdict(float))
    tag_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    use_case_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    model_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    difficulty_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    technique_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    output_type_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    keyword_weights: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    has_behavioral_history: bool = False
    has_profile_hints: bool = False


@dataclass
class ScoreBreakdown:
    total: float
    global_score: float
    behavior_score: float
    text_score: float
    contextual_score: float
    reason_key: str


class RecommendationService:
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
        profile = await self._build_user_profile(viewer)
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

    async def _build_user_profile(self, viewer: User | None) -> UserSignalProfile:
        profile = UserSignalProfile()
        if viewer is None:
            return profile
        restrict_to_unrestricted_categories = not can_view_restricted_category(viewer)

        saved_rows = await self._saved_prompts.list_saved_published_prompts(viewer.id)
        if saved_rows:
            profile.has_behavioral_history = True
        for row in saved_rows:
            profile.saved_prompt_ids.add(row.id)
            self._append_recent_prompt(profile, row.id)
            self._add_prompt_signal(profile, row, weight=3.2)

        recent_events = await self._analytics.list_recent_for_user(
            user_id=viewer.id,
            event_names=[
                AnalyticsEventName.prompt_viewed,
                AnalyticsEventName.prompt_copied,
                AnalyticsEventName.prompt_saved,
            ],
            limit=120,
            from_ts=datetime.now(timezone.utc) - timedelta(days=120),
        )
        prompt_event_ids: list[uuid.UUID] = []
        prompt_event_weights: dict[uuid.UUID, float] = defaultdict(float)
        for event in recent_events:
            prompt_id = self._prompt_id_from_metadata(event.metadata_json)
            if prompt_id is None:
                continue
            try:
                prompt_uuid = uuid.UUID(prompt_id)
            except ValueError:
                continue
            prompt_event_ids.append(prompt_uuid)
            event_name = AnalyticsEventName(event.event_name)
            prompt_event_weights[prompt_uuid] += _ANALYTICS_WEIGHTS.get(event_name, 0.0)

        if prompt_event_weights:
            profile.has_behavioral_history = True
        event_rows = await self._prompts.list_published_by_ids(
            prompt_event_ids,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
        )
        for row in event_rows:
            self._append_recent_prompt(profile, row.id)
            self._add_prompt_signal(profile, row, weight=prompt_event_weights.get(row.id, 0.0))

        mission_events = await self._missions.list_recent_completion_events(user_id=viewer.id, limit=24)
        lesson_ids: list[uuid.UUID] = []
        for event in mission_events:
            if event.prompt_id is not None:
                self._append_recent_prompt(profile, event.prompt_id)
            if event.lesson_id is not None:
                lesson_ids.append(event.lesson_id)
        for lesson_id in list(dict.fromkeys(lesson_ids))[:4]:
            lesson = await self._lessons.get_by_id(lesson_id)
            if lesson is None:
                continue
            self._add_keyword_signal(profile, lesson.title, weight=1.6)

        onboarding_profile = await self._onboarding.get_profile(viewer.id)
        if onboarding_profile is not None:
            hint_tokens: list[str] = []
            if onboarding_profile.role is not None:
                hint_tokens.extend(_PROFILE_KEYWORDS.get(onboarding_profile.role.value, []))
            if onboarding_profile.goal is not None:
                hint_tokens.extend(_PROFILE_KEYWORDS.get(onboarding_profile.goal.value, []))
            if onboarding_profile.ai_context:
                hint_tokens.extend(_PROFILE_KEYWORDS.get(onboarding_profile.ai_context, []))
            for token in dict.fromkeys(hint_tokens):
                profile.keyword_weights[token] += 1.2
            if hint_tokens:
                profile.has_profile_hints = True

            if onboarding_profile.first_win_prompt_id is not None:
                first_win_rows = await self._prompts.list_published_by_ids(
                    [onboarding_profile.first_win_prompt_id],
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
                for row in first_win_rows:
                    self._append_recent_prompt(profile, row.id)
                    self._add_prompt_signal(profile, row, weight=2.2)

        return profile

    async def _candidate_pool(
        self,
        viewer: User | None,
        profile: UserSignalProfile,
        *,
        context: RecommendationContext,
        limit: int,
        seed_prompt: Prompt | None,
        seed_lesson,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
    ) -> list[Prompt]:
        fetch_limit = max(limit * 4, 18)
        top_categories = self._top_weighted_keys(profile.category_weights, 2)
        top_tags = self._top_weighted_keys(profile.tag_weights, 4)
        top_use_cases = self._top_weighted_keys(profile.use_case_weights, 3)
        top_models = self._top_weighted_keys(profile.model_weights, 2)
        query = self._keyword_query(profile.keyword_weights)
        generic_query = "workflow writing research code"
        tasks = [
            self._prompts.list_trending(
                limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            ),
            self._prompts.list_most_saved(
                limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            ),
        ]
        if context in _BEGINNER_CANDIDATE_CONTEXTS or viewer is None:
            tasks.append(
                self._prompts.list_best_for_beginners(
                    limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                )
            )

        candidate_query = query
        if candidate_query is None and viewer is None:
            candidate_query = generic_query
        if candidate_query:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=candidate_query,
                    sort=PromptSort.relevance,
                )
            )
        for category_id in top_categories:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    category_id=category_id,
                    sort=PromptSort.trending,
                )
            )
        for filter_key, values in (
            ("tags", top_tags),
            ("use_cases", top_use_cases),
            ("model_compatibility", top_models),
        ):
            if values:
                tasks.append(
                    self._candidate_query_task(
                        fetch_limit=fetch_limit,
                        restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                        only_free=only_free,
                        sort=PromptSort.trending,
                        **{filter_key: values},
                    )
                )
        if seed_prompt is not None:
            self._append_seed_tasks(
                tasks,
                seed_prompt=seed_prompt,
                fetch_limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                only_free=only_free,
            )
        if seed_lesson is not None:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=seed_lesson.title,
                    sort=PromptSort.relevance,
                )
            )

        batches: list[list[Prompt]] = []
        try:
            for task in tasks:
                batches.append(await task)
        finally:
            for pending in tasks[len(batches) :]:
                pending.close()
        excluded_ids = set(profile.saved_prompt_ids)
        if seed_prompt is not None:
            excluded_ids.add(seed_prompt.id)

        candidates: list[Prompt] = []
        seen_ids: set[uuid.UUID] = set()
        for batch in batches:
            for row in batch:
                if row.id in seen_ids or row.id in excluded_ids:
                    continue
                seen_ids.add(row.id)
                candidates.append(row)
        return candidates

    def _append_seed_tasks(
        self,
        tasks: list,
        *,
        seed_prompt: Prompt,
        fetch_limit: int,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
    ) -> None:
        seed_query = " ".join(filter(None, [seed_prompt.title, seed_prompt.summary or ""])).strip()
        seed_tags = [link.tag.slug for link in seed_prompt.tag_links if link.tag is not None][:4]
        seed_use_cases = [link.use_case.slug for link in seed_prompt.use_case_links if link.use_case is not None][:3]
        seed_models = [link.model.slug for link in seed_prompt.model_links if link.model is not None][:2]
        tasks.append(
            self._candidate_query_task(
                fetch_limit=fetch_limit,
                restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                only_free=only_free,
                category_id=seed_prompt.category_id,
                sort=PromptSort.trending,
            )
        )
        for filter_key, values in (
            ("tags", seed_tags),
            ("use_cases", seed_use_cases),
            ("model_compatibility", seed_models),
        ):
            if values:
                tasks.append(
                    self._candidate_query_task(
                        fetch_limit=fetch_limit,
                        restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                        only_free=only_free,
                        sort=PromptSort.trending,
                        **{filter_key: values},
                    )
                )
        if seed_query:
            tasks.append(
                self._candidate_query_task(
                    fetch_limit=fetch_limit,
                    restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
                    only_free=only_free,
                    q=seed_query,
                    sort=PromptSort.relevance,
                )
            )

    def _candidate_query_task(
        self,
        *,
        fetch_limit: int,
        restrict_to_unrestricted_categories: bool,
        only_free: bool,
        sort: PromptSort,
        **filters,
    ):
        return self._prompts.list_published(
            skip=0,
            limit=fetch_limit,
            sort=sort,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=only_free,
            **filters,
        )

    def _select_diverse_candidates(
        self,
        candidates: Sequence[Prompt],
        *,
        profile: UserSignalProfile,
        context: RecommendationContext,
        seed_prompt: Prompt | None,
        seed_lesson,
        limit: int,
    ) -> list[PromptListItem]:
        scored: list[tuple[Prompt, ScoreBreakdown]] = []
        for row in candidates:
            breakdown = self._score_prompt(
                row,
                profile=profile,
                context=context,
                seed_prompt=seed_prompt,
                seed_lesson=seed_lesson,
            )
            scored.append((row, breakdown))
        scored.sort(key=lambda item: item[1].total, reverse=True)

        selected: list[tuple[Prompt, ScoreBreakdown]] = []
        for _ in range(min(limit, len(scored))):
            best_index = -1
            best_score = -1.0
            for index, (row, breakdown) in enumerate(scored[: max(limit * 4, 12)]):
                adjusted = breakdown.total - self._diversity_penalty(row, selected)
                if adjusted > best_score:
                    best_score = adjusted
                    best_index = index
            if best_index < 0:
                break
            selected.append(scored.pop(best_index))

        items: list[PromptListItem] = []
        for row, breakdown in selected:
            items.append(
                _to_list_item(row).model_copy(update={"recommendation_reason_key": breakdown.reason_key})
            )
        return items

    def _score_prompt(
        self,
        row: Prompt,
        *,
        profile: UserSignalProfile,
        context: RecommendationContext,
        seed_prompt: Prompt | None,
        seed_lesson,
    ) -> ScoreBreakdown:
        global_score = self._global_score(row)
        behavior_score = self._behavior_score(row, profile)
        text_score = self._keyword_match_score(self._prompt_keywords(row), profile.keyword_weights)
        contextual_score = 0.0
        if seed_prompt is not None:
            contextual_score = max(contextual_score, self._prompt_similarity_score(row, seed_prompt))
        if seed_lesson is not None:
            contextual_score = max(contextual_score, self._lesson_similarity_score(row, seed_lesson.title))

        level_bonus = 0.0
        if self._preferred_key(profile.difficulty_weights) == getattr(row.difficulty, "value", None):
            level_bonus = 0.14
        elif getattr(row.difficulty, "value", None) == "beginner":
            level_bonus = 0.12 if not profile.has_behavioral_history else 0.05

        contextual_weight, behavior_weight, text_weight, global_weight, level_weight = _CONTEXT_SCORE_WEIGHTS[
            context
        ]
        total = (
            contextual_score * contextual_weight
            + behavior_score * behavior_weight
            + text_score * text_weight
            + global_score * global_weight
            + level_bonus * level_weight
        )

        return ScoreBreakdown(
            total=total,
            global_score=global_score,
            behavior_score=behavior_score,
            text_score=text_score,
            contextual_score=contextual_score,
            reason_key=self._reason_key(
                behavior_score=behavior_score,
                contextual_score=contextual_score,
                global_score=global_score,
                level_bonus=level_bonus,
                context=context,
                profile=profile,
            ),
        )

    def _reason_key(
        self,
        *,
        behavior_score: float,
        contextual_score: float,
        global_score: float,
        level_bonus: float,
        context: RecommendationContext,
        profile: UserSignalProfile,
    ) -> str:
        if context in {RecommendationContext.prompt_detail, RecommendationContext.after_save} and contextual_score >= 0.34:
            return "recommendation.reason.related"
        if context == RecommendationContext.after_lesson_complete and contextual_score >= 0.2:
            return "recommendation.reason.lesson"
        if behavior_score >= 0.34:
            return "recommendation.reason.behavior"
        if level_bonus >= 0.12:
            return "recommendation.reason.level"
        if global_score >= 0.54:
            return "recommendation.reason.trending"
        if profile.has_behavioral_history or profile.has_profile_hints:
            return "recommendation.reason.explore"
        return "recommendation.reason.curated"

    def _diversity_penalty(
        self,
        candidate: Prompt,
        selected: Sequence[tuple[Prompt, ScoreBreakdown]],
    ) -> float:
        if not selected:
            return 0.0
        penalty = 0.0
        candidate_tags = {link.tag.slug for link in candidate.tag_links if link.tag is not None}
        for picked, _ in selected:
            if picked.category_id == candidate.category_id:
                penalty += 0.12
            if picked.author_id is not None and picked.author_id == candidate.author_id:
                penalty += 0.05
            picked_tags = {link.tag.slug for link in picked.tag_links if link.tag is not None}
            tag_overlap = len(candidate_tags & picked_tags)
            if tag_overlap:
                penalty += min(0.1, tag_overlap * 0.03)
            if picked.difficulty is not None and picked.difficulty == candidate.difficulty:
                penalty += 0.025
        return penalty

    def _global_score(self, row: Prompt) -> float:
        stats = row.stats
        saves = float(stats.save_count if stats else 0)
        copies = float(stats.copy_count if stats else 0)
        views = float(stats.view_count if stats else 0)
        quality_metric = row.quality_metrics.quality_score if row.quality_metrics is not None else 0
        quality = min(max(float(quality_metric), 0.0) / 100.0, 1.0)
        engagement = min(math.log1p(saves * 3.2 + copies * 2.4 + views * 0.35) / 6.0, 1.0)
        created_at = row.created_at if row.created_at.tzinfo is not None else row.created_at.replace(tzinfo=timezone.utc)
        age_days = max((datetime.now(timezone.utc) - created_at).total_seconds() / 86400.0, 0.0)
        recency = 1.0 / (1.0 + age_days / 21.0)
        return engagement * 0.58 + quality * 0.24 + recency * 0.18

    def _behavior_score(self, row: Prompt, profile: UserSignalProfile) -> float:
        if not profile.has_behavioral_history and not profile.has_profile_hints:
            return 0.0
        tags = [link.tag.slug for link in row.tag_links if link.tag is not None]
        use_cases = [link.use_case.slug for link in row.use_case_links if link.use_case is not None]
        models = [link.model.slug for link in row.model_links if link.model is not None]
        difficulty = getattr(row.difficulty, "value", None)
        technique = getattr(row.technique, "value", None)
        output_type = getattr(row.output_type, "value", None)
        score = 0.0
        score += self._single_value_score(row.category_id, profile.category_weights) * 0.32
        score += self._multi_value_score(tags, profile.tag_weights) * 0.22
        score += self._multi_value_score(use_cases, profile.use_case_weights) * 0.18
        score += self._multi_value_score(models, profile.model_weights) * 0.08
        score += self._single_value_score(difficulty, profile.difficulty_weights) * 0.08
        score += self._single_value_score(technique, profile.technique_weights) * 0.06
        score += self._single_value_score(output_type, profile.output_type_weights) * 0.06
        return min(score, 1.0)

    def _prompt_similarity_score(self, row: Prompt, seed: Prompt) -> float:
        row_tags = {link.tag.slug for link in row.tag_links if link.tag is not None}
        seed_tags = {link.tag.slug for link in seed.tag_links if link.tag is not None}
        row_use_cases = {link.use_case.slug for link in row.use_case_links if link.use_case is not None}
        seed_use_cases = {link.use_case.slug for link in seed.use_case_links if link.use_case is not None}
        row_models = {link.model.slug for link in row.model_links if link.model is not None}
        seed_models = {link.model.slug for link in seed.model_links if link.model is not None}
        text_overlap = self._set_overlap(self._prompt_keywords(row), self._prompt_keywords(seed))
        same_category = 1.0 if row.category_id == seed.category_id else 0.0
        same_difficulty = 1.0 if row.difficulty is not None and row.difficulty == seed.difficulty else 0.0
        same_technique = 1.0 if row.technique == seed.technique else 0.0
        return min(
            same_category * 0.32
            + self._set_overlap(row_tags, seed_tags) * 0.26
            + self._set_overlap(row_use_cases, seed_use_cases) * 0.18
            + self._set_overlap(row_models, seed_models) * 0.08
            + text_overlap * 0.1
            + same_difficulty * 0.03
            + same_technique * 0.03,
            1.0,
        )

    def _lesson_similarity_score(self, row: Prompt, lesson_title: str) -> float:
        return self._set_overlap(self._prompt_keywords(row), self._extract_keywords(lesson_title))

    def _prompt_keywords(self, row: Prompt) -> set[str]:
        keywords = set(self._extract_keywords(row.title))
        if row.summary:
            keywords.update(self._extract_keywords(row.summary))
        keywords.update(link.tag.slug for link in row.tag_links if link.tag is not None)
        keywords.update(link.use_case.slug for link in row.use_case_links if link.use_case is not None)
        keywords.update(link.model.slug for link in row.model_links if link.model is not None)
        return keywords

    def _keyword_query(self, weights: dict[str, float], limit: int = 6) -> str | None:
        terms = [key for key, _ in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:limit]]
        query = " ".join(term for term in terms if term and term not in _STOPWORDS).strip()
        return query or None

    def _extract_keywords(self, text: str) -> set[str]:
        terms = {
            token.lower()
            for token in _WORD_RE.findall(text.lower())
            if token.lower() not in _STOPWORDS and not token.isdigit()
        }
        return terms

    def _add_prompt_signal(self, profile: UserSignalProfile, row: Prompt, *, weight: float) -> None:
        if weight <= 0:
            return
        profile.category_weights[row.category_id] += weight
        if row.difficulty is not None:
            profile.difficulty_weights[row.difficulty.value] += weight
        profile.technique_weights[row.technique.value] += weight
        if row.output_type is not None:
            profile.output_type_weights[row.output_type.value] += weight
        for link in row.tag_links:
            if link.tag is not None:
                profile.tag_weights[link.tag.slug] += weight
        for link in row.use_case_links:
            if link.use_case is not None:
                profile.use_case_weights[link.use_case.slug] += weight
        for link in row.model_links:
            if link.model is not None:
                profile.model_weights[link.model.slug] += weight
        self._add_keyword_signal(profile, row.title, weight=weight)
        if row.summary:
            self._add_keyword_signal(profile, row.summary, weight=weight * 0.65)

    def _add_keyword_signal(self, profile: UserSignalProfile, text: str, *, weight: float) -> None:
        for keyword in self._extract_keywords(text):
            profile.keyword_weights[keyword] += weight

    def _append_recent_prompt(self, profile: UserSignalProfile, prompt_id: uuid.UUID) -> None:
        if prompt_id not in profile.recent_prompt_ids:
            profile.recent_prompt_ids.append(prompt_id)

    def _prompt_id_from_metadata(self, metadata: dict | None) -> str | None:
        if not metadata:
            return None
        value = metadata.get("prompt_id")
        return str(value) if value else None

    def _top_weighted_keys(self, weights: dict, limit: int) -> list:
        return [key for key, _ in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:limit]]

    def _preferred_key(self, weights: dict[str, float]) -> str | None:
        if not weights:
            return None
        return max(weights.items(), key=lambda item: item[1])[0]

    def _single_value_score(self, value, weights: dict) -> float:
        if value is None or not weights:
            return 0.0
        top_weight = max(float(weight) for weight in weights.values())
        if top_weight <= 0:
            return 0.0
        return min(float(weights.get(value, 0.0)) / top_weight, 1.0)

    def _multi_value_score(self, values: Sequence[str], weights: dict[str, float]) -> float:
        if not values or not weights:
            return 0.0
        top_total = sum(weight for _, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:4])
        if top_total <= 0:
            return 0.0
        raw = sum(float(weights.get(value, 0.0)) for value in values)
        return min(raw / float(top_total), 1.0)

    def _keyword_match_score(self, values: set[str], weights: dict[str, float]) -> float:
        if not values or not weights:
            return 0.0
        top_total = sum(weight for _, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)[:8])
        if top_total <= 0:
            return 0.0
        raw = sum(float(weights.get(value, 0.0)) for value in values)
        return min(raw / float(top_total), 1.0)

    def _set_overlap(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        union = left | right
        if not union:
            return 0.0
        return len(left & right) / len(union)

    def _recommendation_strategy(
        self,
        context: RecommendationContext,
        profile: UserSignalProfile,
    ) -> RecommendationStrategy:
        if context in _CONTEXTUAL_STRATEGY_CONTEXTS:
            return RecommendationStrategy.contextual
        if profile.has_behavioral_history or profile.has_profile_hints:
            return RecommendationStrategy.personalized
        return RecommendationStrategy.cold_start

    def _should_only_show_free(self, viewer: User | None, context: RecommendationContext) -> bool:
        if viewer is None or can_view_premium_content(viewer):
            return False
        return context in {
            RecommendationContext.dashboard,
            RecommendationContext.after_save,
            RecommendationContext.after_lesson_complete,
        }
