from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from app.core.errors import NotFoundError
from app.core.tiers import can_view_premium_content, can_view_restricted_category
from app.infrastructure.db.models import Prompt, PromptStatus, User
from app.modules.catalog.model.prompt import PromptRead, StoreUnlockOffer
from app.modules.catalog.service.prompt_projection import apply_read_gating


class PromptServiceReadMixin:
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
            read = apply_read_gating(row, viewer=viewer, locked=not access.has_access, access=access)
        else:
            locked, unlock_offer = await self._resolve_unlock_offer(row, viewer)
            read = apply_read_gating(row, viewer=viewer, locked=locked, unlock_offer=unlock_offer, access=None)

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

    async def track_copy(self, prompt_id: uuid.UUID, viewer: User | None) -> None:
        row = await self._repo.get_by_id(prompt_id)
        if row is None or row.status != PromptStatus.published:
            raise NotFoundError("prompt", str(prompt_id))
        if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
            raise NotFoundError("prompt", str(prompt_id))
        await self._repo.increment_copy_count(prompt_id)
