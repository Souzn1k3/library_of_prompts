from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from app.infrastructure.db.models import (
    Category,
    ContributorProfile,
    Prompt,
    PromptQualityMetric,
    PromptModelCompatibility,
    PromptStats,
    PromptTag,
    PromptUseCase,
    User,
)


class PromptRepositoryProjectionMixin:
    def _prompt_relation_load_options(self):
        return (
            selectinload(Prompt.use_case_links).selectinload(PromptUseCase.use_case),
            selectinload(Prompt.model_links).selectinload(PromptModelCompatibility.model),
            selectinload(Prompt.tag_links).selectinload(PromptTag.tag),
        )

    def _prompt_detail_load_options(self):
        return (
            joinedload(Prompt.category),
            joinedload(Prompt.stats),
            joinedload(Prompt.quality_metrics),
            joinedload(Prompt.pricing),
            *self._prompt_relation_load_options(),
            joinedload(Prompt.author).joinedload(User.contributor_profile),
        )

    def _list_load_options(self):
        return (
            contains_eager(Prompt.category),
            contains_eager(Prompt.stats),
            contains_eager(Prompt.quality_metrics),
            selectinload(Prompt.pricing),
            *self._prompt_relation_load_options(),
        )

    def _author_load_option(self, *, eager: bool):
        if eager:
            return contains_eager(Prompt.author).contains_eager(User.contributor_profile)
        return selectinload(Prompt.author).selectinload(User.contributor_profile)

    def _published_query(self, selection, *, include_stats: bool, include_contributor: bool):
        stmt = select(selection).select_from(Prompt).join(Category, Prompt.category_id == Category.id)
        if include_stats:
            stmt = stmt.outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id).outerjoin(
                PromptQualityMetric, PromptQualityMetric.prompt_id == Prompt.id
            )
        if include_contributor:
            stmt = stmt.outerjoin(User, User.id == Prompt.author_id).outerjoin(
                ContributorProfile, ContributorProfile.user_id == User.id
            )
        return stmt
