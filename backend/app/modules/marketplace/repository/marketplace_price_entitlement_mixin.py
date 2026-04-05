from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import PromptAccessSource, PromptEntitlement, PromptPrice


class MarketplacePriceEntitlementMixin:
    async def get_prompt_price(self, prompt_id: uuid.UUID) -> PromptPrice | None:
        result = await self._session.execute(select(PromptPrice).where(PromptPrice.prompt_id == prompt_id))
        return result.scalar_one_or_none()

    async def list_prompt_prices(self, prompt_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, PromptPrice]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return {}
        result = await self._session.execute(select(PromptPrice).where(PromptPrice.prompt_id.in_(ids)))
        return {row.prompt_id: row for row in result.scalars().all()}

    async def get_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        for_update: bool = False,
    ) -> PromptEntitlement | None:
        stmt = (
            select(PromptEntitlement)
            .options(selectinload(PromptEntitlement.purchase))
            .where(
                PromptEntitlement.user_id == user_id,
                PromptEntitlement.prompt_id == prompt_id,
                PromptEntitlement.revoked_at.is_(None),
            )
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_entitled_prompt_ids(
        self,
        *,
        user_id: uuid.UUID,
        prompt_ids: Sequence[uuid.UUID],
    ) -> set[uuid.UUID]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return set()
        result = await self._session.execute(
            select(PromptEntitlement.prompt_id).where(
                PromptEntitlement.user_id == user_id,
                PromptEntitlement.prompt_id.in_(ids),
                PromptEntitlement.revoked_at.is_(None),
            )
        )
        return {row[0] for row in result.all()}

    async def create_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        source: PromptAccessSource,
        purchase_id: uuid.UUID | None = None,
        meta: dict | None = None,
        granted_at: datetime | None = None,
    ) -> PromptEntitlement:
        entitlement = PromptEntitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=source,
            purchase_id=purchase_id,
            meta=meta,
            granted_at=granted_at or datetime.now(timezone.utc),
        )
        self._session.add(entitlement)
        await self._session.flush()
        await self._session.refresh(entitlement)
        return entitlement

    async def try_create_entitlement(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
        source: PromptAccessSource,
        purchase_id: uuid.UUID | None = None,
        meta: dict | None = None,
        granted_at: datetime | None = None,
    ) -> PromptEntitlement | None:
        entitlement = PromptEntitlement(
            user_id=user_id,
            prompt_id=prompt_id,
            source=source,
            purchase_id=purchase_id,
            meta=meta,
            granted_at=granted_at or datetime.now(timezone.utc),
        )
        try:
            async with self._session.begin_nested():
                self._session.add(entitlement)
                await self._session.flush()
        except IntegrityError:
            return None
        await self._session.refresh(entitlement)
        return entitlement

    async def save_entitlement(self, entitlement: PromptEntitlement) -> PromptEntitlement:
        await self._session.flush()
        await self._session.refresh(entitlement)
        return entitlement
