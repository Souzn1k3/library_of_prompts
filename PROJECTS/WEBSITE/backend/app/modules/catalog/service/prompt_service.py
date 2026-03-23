import uuid
from collections.abc import Sequence
from typing import Protocol

from app.core.errors import NotFoundError
from app.core.tiers import (
    can_view_premium_content,
    can_view_restricted_category,
    mask_body_if_needed,
)
from app.infrastructure.db.models import Prompt, PromptStatus, PromptTechnique, User
from app.modules.catalog.model.prompt import PromptListItem, PromptRead
from app.modules.catalog.repository.prompt_repository import PromptRepository


class PromptRepositoryProtocol(Protocol):
    async def list_published(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        restrict_to_unrestricted_categories: bool = False,
    ) -> Sequence[Prompt]: ...

    async def count_published(
        self,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
        restrict_to_unrestricted_categories: bool = False,
    ) -> int: ...

    async def get_by_slug(self, slug: str) -> Prompt | None: ...

    async def get_by_id(self, prompt_id: uuid.UUID) -> Prompt | None: ...


def _to_list_item(row: Prompt) -> PromptListItem:
    return PromptListItem.model_validate(row)


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
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
    ) -> list[PromptListItem]:
        rows = await self._repo.list_published(
            skip=skip,
            limit=limit,
            q=q,
            category_id=category_id,
            technique=technique,
            restrict_to_unrestricted_categories=self._restrict_catalog(viewer),
        )
        return [_to_list_item(r) for r in rows]

    async def count_published(
        self,
        viewer: User | None,
        *,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
        technique: PromptTechnique | None = None,
    ) -> int:
        return await self._repo.count_published(
            q=q,
            category_id=category_id,
            technique=technique,
            restrict_to_unrestricted_categories=self._restrict_catalog(viewer),
        )

    async def get_by_slug(self, slug: str, viewer: User | None) -> PromptRead:
        row = await self._repo.get_by_slug(slug)
        if row is None:
            raise NotFoundError("prompt", slug)
        if row.status != PromptStatus.published:
            raise NotFoundError("prompt", slug)
        return _apply_read_gating(row, viewer)

    async def get_by_id(self, prompt_id: uuid.UUID, viewer: User | None) -> PromptRead:
        row = await self._repo.get_by_id(prompt_id)
        if row is None:
            raise NotFoundError("prompt", str(prompt_id))
        if row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        return _apply_read_gating(row, viewer)
