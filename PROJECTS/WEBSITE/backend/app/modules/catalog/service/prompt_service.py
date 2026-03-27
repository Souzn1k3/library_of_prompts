import uuid
from collections.abc import Sequence
from typing import Protocol

from app.core.errors import NotFoundError
from app.core.tiers import can_view_premium_content, can_view_restricted_category, mask_body_if_needed
from app.infrastructure.db.models import (
    ModelCompatibility,
    Prompt,
    PromptDifficulty,
    PromptOutputType,
    PromptStatus,
    PromptTechnique,
    Tag,
    UseCase,
    User,
)
from app.modules.catalog.model.prompt import (
    DiscoverySections,
    PromptDiscoveryFilters,
    PromptListItem,
    PromptRead,
    PromptSort,
)


class PromptRepositoryProtocol(Protocol):
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
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        sort: PromptSort = PromptSort.relevance,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> Sequence[Prompt]: ...

    async def count_published(
        self,
        *,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        restrict_to_unrestricted_categories: bool = False,
        only_free: bool = False,
    ) -> int: ...

    async def get_by_slug(self, slug: str) -> Prompt | None: ...

    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None: ...

    async def list_trending(self, *, limit: int, restrict_to_unrestricted_categories: bool) -> Sequence[Prompt]: ...

    async def list_best_for_beginners(
        self,
        *,
        limit: int,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]: ...

    async def list_most_saved(self, *, limit: int, restrict_to_unrestricted_categories: bool) -> Sequence[Prompt]: ...

    async def list_related(
        self,
        *,
        prompt: Prompt,
        limit: int = 6,
        restrict_to_unrestricted_categories: bool,
    ) -> Sequence[Prompt]: ...

    async def list_use_cases(self) -> Sequence[UseCase]: ...

    async def list_model_compatibility(self) -> Sequence[ModelCompatibility]: ...

    async def list_tags(self) -> Sequence[Tag]: ...

    async def increment_copy_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None: ...

    async def increment_view_count(self, prompt_id: uuid.UUID, amount: int = 1) -> None: ...


def _to_list_item(row: Prompt) -> PromptListItem:
    contributor = row.author.contributor_profile if row.author and row.author.contributor_profile else None
    quality_score = 0
    if row.quality_metrics is not None:
        quality_score = row.quality_metrics.quality_score
    elif row.stats is not None:
        quality_score = row.stats.quality_score
    return PromptListItem(
        id=row.id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        status=row.status,
        technique=row.technique,
        moderation_state=row.moderation_state,
        category_id=row.category_id,
        author_id=row.author_id,
        created_at=row.created_at,
        is_premium=row.is_premium,
        difficulty=row.difficulty,
        output_type=row.output_type,
        use_cases=[link.use_case.slug for link in row.use_case_links if link.use_case is not None],
        model_compatibility=[link.model.slug for link in row.model_links if link.model is not None],
        tags=[link.tag.slug for link in row.tag_links if link.tag is not None],
        save_count=row.stats.save_count if row.stats else 0,
        copy_count=row.stats.copy_count if row.stats else 0,
        quality_score=quality_score,
        contributor_slug=contributor.slug if contributor else None,
        contributor_tier=contributor.reputation_tier if contributor else None,
        contributor_reputation_score=contributor.reputation_score if contributor else None,
    )


def _apply_read_gating(row: Prompt, viewer: User | None) -> PromptRead:
    if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
        raise NotFoundError("prompt", row.slug)

    locked = bool(row.is_premium) and not can_view_premium_content(viewer)
    body = mask_body_if_needed(body=row.body, locked=locked)
    base = _to_list_item(row)
    return PromptRead(**base.model_dump(), body=body, body_locked=locked)


class PromptService:
    def __init__(self, repo: PromptRepositoryProtocol) -> None:
        self._repo = repo

    def _restrict_catalog(self, viewer: User | None) -> bool:
        return not can_view_restricted_category(viewer)

    async def list_published(
        self,
        viewer: User | None,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        sort: PromptSort = PromptSort.relevance,
        only_free: bool = False,
    ) -> list[PromptListItem]:
        rows = await self._repo.list_published(
            skip=skip,
            limit=limit,
            q=q,
            contributor_slug=contributor_slug,
            category_id=category_id,
            technique=technique,
            difficulty=difficulty,
            output_type=output_type,
            use_cases=use_cases,
            model_compatibility=model_compatibility,
            tags=tags,
            sort=sort,
            restrict_to_unrestricted_categories=self._restrict_catalog(viewer),
            only_free=only_free,
        )
        return [_to_list_item(r) for r in rows]

    async def count_published(
        self,
        viewer: User | None,
        *,
        q: str | None = None,
        contributor_slug: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        difficulty: PromptDifficulty | None = None,
        output_type: PromptOutputType | None = None,
        use_cases: Sequence[str] | None = None,
        model_compatibility: Sequence[str] | None = None,
        tags: Sequence[str] | None = None,
        only_free: bool = False,
    ) -> int:
        return await self._repo.count_published(
            q=q,
            contributor_slug=contributor_slug,
            category_id=category_id,
            technique=technique,
            difficulty=difficulty,
            output_type=output_type,
            use_cases=use_cases,
            model_compatibility=model_compatibility,
            tags=tags,
            restrict_to_unrestricted_categories=self._restrict_catalog(viewer),
            only_free=only_free,
        )

    async def get_by_slug(self, slug: str, viewer: User | None) -> PromptRead:
        row = await self._repo.get_by_slug(slug)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", slug)
        read = _apply_read_gating(row, viewer)
        await self._repo.increment_view_count(row.id)
        return read

    async def get_by_id(self, prompt_id: uuid.UUID, viewer: User | None) -> PromptRead:
        row = await self._repo.get_by_id(prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        read = _apply_read_gating(row, viewer)
        await self._repo.increment_view_count(row.id)
        return read

    async def discovery_filters(self) -> PromptDiscoveryFilters:
        use_cases = await self._repo.list_use_cases()
        models = await self._repo.list_model_compatibility()
        tags = await self._repo.list_tags()
        return PromptDiscoveryFilters(
            use_cases=[{"slug": row.slug, "name": row.name} for row in use_cases],
            model_compatibility=[{"slug": row.slug, "name": row.name} for row in models],
            tags=[{"slug": row.slug, "name": row.name} for row in tags],
            difficulties=[PromptDifficulty.beginner.value, PromptDifficulty.intermediate.value, PromptDifficulty.advanced.value],
            output_types=[PromptOutputType.text.value, PromptOutputType.code.value, PromptOutputType.structured.value],
            sorts=[
                PromptSort.relevance.value,
                PromptSort.trending.value,
                PromptSort.most_used.value,
                PromptSort.newest.value,
                PromptSort.most_saved.value,
            ],
        )

    async def discovery_sections(self, viewer: User | None, limit: int = 8) -> DiscoverySections:
        restrict = self._restrict_catalog(viewer)
        trending = await self._repo.list_trending(limit=limit, restrict_to_unrestricted_categories=restrict)
        beginner = await self._repo.list_best_for_beginners(
            limit=limit,
            restrict_to_unrestricted_categories=restrict,
        )
        most_saved = await self._repo.list_most_saved(limit=limit, restrict_to_unrestricted_categories=restrict)
        return DiscoverySections(
            trending=[_to_list_item(row) for row in trending],
            best_for_beginners=[_to_list_item(row) for row in beginner],
            most_saved=[_to_list_item(row) for row in most_saved],
        )

    async def related_prompts(self, slug: str, viewer: User | None, *, limit: int = 6) -> list[PromptListItem]:
        row = await self._repo.get_by_slug(slug)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", slug)
        if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
            raise NotFoundError("prompt", slug)
        related = await self._repo.list_related(
            prompt=row,
            limit=limit,
            restrict_to_unrestricted_categories=self._restrict_catalog(viewer),
        )
        return [_to_list_item(item) for item in related]

    async def track_copy(self, prompt_id: uuid.UUID, viewer: User | None) -> None:
        row = await self._repo.get_by_id(prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
            raise NotFoundError("prompt", str(prompt_id))
        await self._repo.increment_copy_count(prompt_id)
