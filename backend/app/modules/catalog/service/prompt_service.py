import uuid
from collections.abc import Sequence
from typing import Protocol

from app.infrastructure.db.models import (
    ModelCompatibility,
    Prompt,
    PromptDifficulty,
    PromptOutputType,
    PromptTechnique,
    Tag,
    UseCase,
    User,
)
from app.modules.catalog.model.prompt import PromptRead, PromptSort
from app.modules.catalog.service.prompt_catalog_mixin import PromptServiceCatalogMixin
from app.modules.catalog.service.prompt_projection import to_list_item
from app.modules.catalog.service.prompt_read_mixin import PromptServiceReadMixin
from app.modules.catalog.service.prompt_support_mixin import PromptServiceSupportMixin
from app.modules.economy.repository.store_repository import StoreRepository
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


class PromptService(PromptServiceCatalogMixin, PromptServiceReadMixin, PromptServiceSupportMixin):
    def __init__(
        self,
        repo: PromptRepositoryProtocol,
        store_repo: StoreRepository | None = None,
        marketplace: MarketplaceService | None = None,
    ) -> None:
        self._repo = repo
        self._store_repo = store_repo
        self._marketplace = marketplace

    async def get_by_slug(
        self,
        slug: str,
        viewer: User | None,
        *,
        auto_grant_included_unlock: bool = True,
    ) -> PromptRead:
        return await super().get_by_slug(
            slug,
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
        return await super().get_by_id(
            prompt_id,
            viewer,
            auto_grant_included_unlock=auto_grant_included_unlock,
        )


# Backward-compatible projection export used by recommendation service.
_to_list_item = to_list_item
