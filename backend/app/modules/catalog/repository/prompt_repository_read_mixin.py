from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.orm import contains_eager, joinedload

from app.infrastructure.db.models import (
    Category,
    ContributorProfile,
    ModerationState,
    Prompt,
    PromptDifficulty,
    PromptQualityMetric,
    PromptStats,
    PromptStatus,
    PromptTag,
    PromptTechnique,
    PromptUseCase,
    User,
)
from app.modules.catalog.model.prompt import PromptSort


class PromptRepositoryReadMixin:
    async def list_published(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type=None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        sort: PromptSort = PromptSort.relevance,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> Sequence[Prompt]:
        include_text_score = sort == PromptSort.relevance
        include_contributor_score = sort in {PromptSort.relevance, PromptSort.trending} or bool(contributor_slug)

        ranking = self._search_ranking(
            q,
            include_text_score=include_text_score,
            include_contributor_score=include_contributor_score,
        )
        filters = self._search_filters(
            q=q,
            contributor_slug=contributor_slug,
            category_id=category_id,
            technique=technique,
            difficulty=difficulty,
            output_type=output_type,
            use_cases=use_cases,
            model_compatibility=model_compatibility,
            tags=tags,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=only_free,
        )

        stmt = self._published_query(
            Prompt,
            include_stats=True,
            include_contributor=include_contributor_score,
        ).where(filters)
        stmt = stmt.options(
            self._author_load_option(eager=include_contributor_score),
            *self._list_load_options(),
        )

        stmt = self._apply_sort(stmt, sort=sort, ranking=ranking).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def count_published(
        self,
        *,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type=None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> int:
        filters = self._search_filters(
            q=q,
            contributor_slug=contributor_slug,
            category_id=category_id,
            technique=technique,
            difficulty=difficulty,
            output_type=output_type,
            use_cases=use_cases,
            model_compatibility=model_compatibility,
            tags=tags,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=only_free,
        )
        stmt = self._published_query(
            func.count(),
            include_stats=False,
            include_contributor=bool(contributor_slug),
        ).where(filters)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_trending(self, *, limit: int = 8, restrict_to_unrestricted_categories: bool) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            sort=PromptSort.trending,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=False,
        )

    async def list_best_for_beginners(
        self,
        *,
        limit: int = 8,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            difficulty=PromptDifficulty.beginner,
            sort=PromptSort.relevance,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=True,
        )

    async def list_most_saved(
        self,
        *,
        limit: int = 8,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        return await self.list_published(
            skip=0,
            limit=limit,
            sort=PromptSort.most_saved,
            restrict_to_unrestricted_categories=restrict_to_unrestricted_categories,
            only_free=False,
        )

    async def get_by_slug(self, slug: str) -> Prompt | None:
        return await self._get_prompt(Prompt.slug == slug)

    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None:
        return await self._get_prompt(Prompt.id == prompt_id)

    async def list_published_by_ids(
        self,
        prompt_ids: Sequence[uuid.UUID],
        *,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return []

        stmt = (
            select(Prompt)
            .options(*self._prompt_detail_load_options())
            .where(
                Prompt.id.in_(ids),
                Prompt.status == PromptStatus.published,
            )
        )
        if restrict_to_unrestricted_categories:
            stmt = stmt.join(Category, Prompt.category_id == Category.id).where(Category.is_restricted.is_(False))

        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_related(
        self,
        *,
        prompt: Prompt,
        limit: int = 6,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]:
        tag_ids = [link.tag_id for link in prompt.tag_links]
        use_case_ids = [link.use_case_id for link in prompt.use_case_links]

        tag_match_subq = (
            select(PromptTag.prompt_id, func.count().label("tag_match_count"))
            .where(PromptTag.tag_id.in_(tag_ids))
            .group_by(PromptTag.prompt_id)
            .subquery()
            if tag_ids
            else None
        )
        use_case_match_subq = (
            select(PromptUseCase.prompt_id, func.count().label("use_case_match_count"))
            .where(PromptUseCase.use_case_id.in_(use_case_ids))
            .group_by(PromptUseCase.prompt_id)
            .subquery()
            if use_case_ids
            else None
        )

        stmt = (
            select(Prompt)
            .join(Category, Prompt.category_id == Category.id)
            .outerjoin(PromptStats, PromptStats.prompt_id == Prompt.id)
            .outerjoin(PromptQualityMetric, PromptQualityMetric.prompt_id == Prompt.id)
            .outerjoin(User, User.id == Prompt.author_id)
            .outerjoin(ContributorProfile, ContributorProfile.user_id == User.id)
            .options(
                contains_eager(Prompt.stats),
                contains_eager(Prompt.quality_metrics),
                *self._prompt_relation_load_options(),
                self._author_load_option(eager=True),
            )
            .where(
                Prompt.status == PromptStatus.published,
                Prompt.id != prompt.id,
            )
        )
        if restrict_to_unrestricted_categories:
            stmt = stmt.where(Category.is_restricted.is_(False))
        if tag_match_subq is not None:
            stmt = stmt.outerjoin(tag_match_subq, tag_match_subq.c.prompt_id == Prompt.id)
        if use_case_match_subq is not None:
            stmt = stmt.outerjoin(use_case_match_subq, use_case_match_subq.c.prompt_id == Prompt.id)

        related_score = (
            case((Prompt.category_id == prompt.category_id, 1.2), else_=0.0)
            + case((Prompt.technique == prompt.technique, 0.8), else_=0.0)
            + (func.coalesce(tag_match_subq.c.tag_match_count, 0) * 1.5 if tag_match_subq is not None else 0.0)
            + (
                func.coalesce(use_case_match_subq.c.use_case_match_count, 0) * 1.2
                if use_case_match_subq is not None
                else 0.0
            )
            + (func.coalesce(PromptStats.save_count, 0) * 0.05)
            + (func.coalesce(ContributorProfile.reputation_score, 0) * 0.01)
        )

        stmt = stmt.order_by(related_score.desc(), Prompt.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_moderation_queue(self, *, skip: int = 0, limit: int = 50) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .outerjoin(User, User.id == Prompt.author_id)
            .outerjoin(ContributorProfile, ContributorProfile.user_id == User.id)
            .options(
                joinedload(Prompt.category),
                self._author_load_option(eager=True),
            )
            .where(
                Prompt.status == PromptStatus.draft,
                Prompt.moderation_state == ModerationState.pending,
            )
            .order_by(
                func.coalesce(ContributorProfile.reputation_score, 0).desc(),
                Prompt.created_at.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    async def list_by_author(
        self,
        author_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Prompt]:
        stmt = (
            select(Prompt)
            .where(Prompt.author_id == author_id)
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
