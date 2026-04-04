import uuid
from collections.abc import Awaitable, Callable, Sequence
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
    StoreUnlockOffer,
)
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.marketplace.model.marketplace import PromptAccessRead, PromptPriceRead
from app.modules.marketplace.service.marketplace_service import MarketplaceService


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


def _to_list_item(
    row: Prompt,
    *,
    access: PromptAccessRead | None = None,
) -> PromptListItem:
    contributor = row.author.contributor_profile if row.author and row.author.contributor_profile else None
    quality_score = row.quality_metrics.quality_score if row.quality_metrics is not None else 0
    price = (
        PromptPriceRead(
            price_rub=row.pricing.price_rub,
            price_lumens=row.pricing.price_lumens,
            commission_percent=row.pricing.commission_percent,
        )
        if row.pricing is not None and row.pricing.is_active
        else None
    )
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
        is_paid=bool(row.pricing and row.pricing.is_active),
        difficulty=row.difficulty,
        output_type=row.output_type,
        price=price,
        access=access,
        use_cases=[link.use_case.slug for link in row.use_case_links if link.use_case is not None],
        model_compatibility=[link.model.slug for link in row.model_links if link.model is not None],
        tags=[link.tag.slug for link in row.tag_links if link.tag is not None],
        save_count=row.stats.save_count if row.stats else 0,
        copy_count=row.stats.copy_count if row.stats else 0,
        quality_score=quality_score,
        contributor_slug=contributor.slug if contributor else None,
        contributor_tier=contributor.reputation_tier if contributor else None,
        contributor_reputation_score=contributor.reputation_score if contributor else None,
        author_display_name=row.author.display_name if row.author is not None else None,
    )


def _apply_read_gating(
    row: Prompt,
    *,
    viewer: User | None,
    locked: bool,
    unlock_offer: StoreUnlockOffer | None = None,
    access: PromptAccessRead | None = None,
) -> PromptRead:
    if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
        raise NotFoundError("prompt", row.slug)

    body = mask_body_if_needed(body=row.body, locked=locked)
    base = _to_list_item(row, access=access)
    return PromptRead(**base.model_dump(), body=body, body_locked=locked, unlock_offer=unlock_offer)


class PromptService:
    def __init__(
        self,
        repo: PromptRepositoryProtocol,
        store_repo: StoreRepository | None = None,
        marketplace: MarketplaceService | None = None,
    ) -> None:
        self._repo = repo
        self._store_repo = store_repo
        self._marketplace = marketplace

    def _restrict_catalog(self, viewer: User | None) -> bool:
        return not can_view_restricted_category(viewer)

    @staticmethod
    def _contributor_tier_value(row: Prompt) -> str | None:
        if row.author is None or row.author.contributor_profile is None:
            return None
        return row.author.contributor_profile.reputation_tier.value

    async def _attach_author_rating(self, read: PromptRead, row: Prompt) -> None:
        if self._marketplace is None or row.author_id is None:
            return
        summary = await self._marketplace.seller_summary(
            seller_user_id=row.author_id,
            reputation_tier=self._contributor_tier_value(row),
            review_limit=3,
        )
        read.author_rating_average = summary.rating_average
        read.author_rating_count = summary.review_count

    @staticmethod
    def _published_or_not_found(row: Prompt | None, *, key: str) -> Prompt:
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", key)
        return row

    async def _load_published_prompt(
        self,
        *,
        loader: Callable[[], Awaitable[Prompt | None]],
        key: str,
    ) -> Prompt:
        row = await loader()
        return self._published_or_not_found(row, key=key)

    async def _build_prompt_read(
        self,
        row: Prompt,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool,
    ) -> PromptRead:
        if self._marketplace is not None and row.pricing is not None and row.pricing.is_active:
            access = await self._marketplace.resolve_prompt_access(
                row,
                viewer,
                auto_grant_included_unlock=auto_grant_included_unlock,
            )
            read = _apply_read_gating(row, viewer=viewer, locked=not access.has_access, access=access)
        else:
            locked, unlock_offer = await self._resolve_unlock_offer(row, viewer)
            read = _apply_read_gating(row, viewer=viewer, locked=locked, unlock_offer=unlock_offer, access=None)

        await self._attach_author_rating(read, row)
        await self._repo.increment_view_count(row.id)
        return read

    async def _resolve_unlock_offer(
        self,
        row: Prompt,
        viewer: User | None,
    ) -> tuple[bool, StoreUnlockOffer | None]:
        locked = bool(row.is_premium) and not can_view_premium_content(viewer)
        if not locked or viewer is None or self._store_repo is None:
            return locked, None

        has_personal_access = await self._store_repo.user_has_prompt_access(user_id=viewer.id, prompt_id=row.id)
        if has_personal_access:
            return False, None

        item = await self._store_repo.find_active_unlock_offer_for_prompt(row.id)
        if item is None:
            return True, None

        return (
            True,
            StoreUnlockOffer(
                item_slug=item.slug,
                item_title=item.title,
                price=item.price,
                kind=item.kind,
            ),
        )

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
        return [_to_list_item(r, access=access_map.get(r.id)) for r in rows]

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

    async def get_by_slug(
        self,
        slug: str,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = True,
    ) -> PromptRead:
        row = await self._load_published_prompt(loader=lambda: self._repo.get_by_slug(slug), key=slug)
        return await self._build_prompt_read(
            row,
            viewer,
            auto_grant_included_unlock=auto_grant_included_unlock,
        )

    async def get_by_id(
        self,
        prompt_id: uuid.UUID,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = True,
    ) -> PromptRead:
        key = str(prompt_id)
        row = await self._load_published_prompt(loader=lambda: self._repo.get_by_id(prompt_id), key=key)
        return await self._build_prompt_read(
            row,
            viewer,
            auto_grant_included_unlock=auto_grant_included_unlock,
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
            trending=[_to_list_item(row, access=access_map.get(row.id)) for row in trending],
            best_for_beginners=[_to_list_item(row, access=access_map.get(row.id)) for row in beginner],
            most_saved=[_to_list_item(row, access=access_map.get(row.id)) for row in most_saved],
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
        return [_to_list_item(item, access=access_map.get(item.id)) for item in related]

    async def track_copy(self, prompt_id: uuid.UUID, viewer: User | None) -> None:
        row = await self._repo.get_by_id(prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
            raise NotFoundError("prompt", str(prompt_id))
        await self._repo.increment_copy_count(prompt_id)
