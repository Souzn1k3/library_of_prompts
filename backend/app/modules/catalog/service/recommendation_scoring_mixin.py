from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime, timezone

from app.core.tiers import can_view_premium_content
from app.infrastructure.db.models import Prompt
from app.modules.catalog.model.prompt import PromptListItem
from app.modules.catalog.model.recommendation import RecommendationContext, RecommendationStrategy
from app.modules.catalog.service.prompt_service import _to_list_item
from app.modules.catalog.service.recommendation_constants import (
    CONTEXT_SCORE_WEIGHTS,
    CONTEXTUAL_STRATEGY_CONTEXTS,
    ScoreBreakdown,
    UserSignalProfile,
)


class RecommendationScoringMixin:
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

        contextual_weight, behavior_weight, text_weight, global_weight, level_weight = CONTEXT_SCORE_WEIGHTS[context]
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

    def _recommendation_strategy(
        self,
        context: RecommendationContext,
        profile: UserSignalProfile,
    ) -> RecommendationStrategy:
        if context in CONTEXTUAL_STRATEGY_CONTEXTS:
            return RecommendationStrategy.contextual
        if profile.has_behavioral_history or profile.has_profile_hints:
            return RecommendationStrategy.personalized
        return RecommendationStrategy.cold_start

    def _should_only_show_free(self, viewer, context: RecommendationContext) -> bool:
        if viewer is None or can_view_premium_content(viewer):
            return False
        return context in {
            RecommendationContext.dashboard,
            RecommendationContext.after_save,
            RecommendationContext.after_lesson_complete,
        }
