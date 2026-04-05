from __future__ import annotations

import uuid
from collections.abc import Sequence

from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category
from app.infrastructure.db.models import PromptDifficulty, PromptOutputType, PromptStatus, PromptTechnique, User
from app.modules.catalog.model.prompt import DiscoverySections, PromptDiscoveryFilters, PromptListItem, PromptSort
from app.modules.catalog.service.prompt_projection import to_list_item


class PromptServiceCatalogMixin:
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
        access_map = await self._marketplace.build_access_map(list(rows), viewer) if self._marketplace is not None else {}
        return [to_list_item(r, access=access_map.get(r.id)) for r in rows]

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
        access_map = (
            await self._marketplace.build_access_map(list(trending) + list(beginner) + list(most_saved), viewer)
            if self._marketplace is not None
            else {}
        )
        return DiscoverySections(
            trending=[to_list_item(row, access=access_map.get(row.id)) for row in trending],
            best_for_beginners=[to_list_item(row, access=access_map.get(row.id)) for row in beginner],
            most_saved=[to_list_item(row, access=access_map.get(row.id)) for row in most_saved],
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
        access_map = await self._marketplace.build_access_map(list(related), viewer) if self._marketplace is not None else {}
        return [to_list_item(item, access=access_map.get(item.id)) for item in related]
