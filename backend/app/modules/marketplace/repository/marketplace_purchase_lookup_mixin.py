from __future__ import annotations

import uuid

from sqlalchemy import select

from app.infrastructure.db.models import PromptPurchase, PurchaseStatus


class MarketplacePurchaseLookupMixin:
    async def get_purchase_by_client_token(
        self,
        *,
        user_id: uuid.UUID,
        client_token: str,
    ) -> PromptPurchase | None:
        stmt = self._purchase_stmt().where(
            PromptPurchase.user_id == user_id,
            PromptPurchase.client_token == client_token,
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_id(self, purchase_id: uuid.UUID, *, for_update: bool = False) -> PromptPurchase | None:
        stmt = self._purchase_stmt().where(PromptPurchase.id == purchase_id).limit(1)
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_provider_checkout_id(self, checkout_id: str) -> PromptPurchase | None:
        stmt = self._purchase_stmt().where(PromptPurchase.provider_checkout_id == checkout_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_purchase_by_provider_payment_id(self, payment_id: str) -> PromptPurchase | None:
        stmt = self._purchase_stmt().where(PromptPurchase.provider_payment_id == payment_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_completed_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            self._purchase_stmt()
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.completed,
            )
            .order_by(PromptPurchase.completed_at.desc().nullslast(), PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.pending,
            )
            .order_by(PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent_user_purchases(self, user_id: uuid.UUID, *, limit: int = 12) -> list[PromptPurchase]:
        stmt = self._purchase_stmt().where(PromptPurchase.user_id == user_id).order_by(PromptPurchase.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_reviewable_purchase(
        self,
        *,
        user_id: uuid.UUID,
        prompt_id: uuid.UUID,
    ) -> PromptPurchase | None:
        stmt = (
            self._purchase_stmt()
            .where(
                PromptPurchase.user_id == user_id,
                PromptPurchase.prompt_id == prompt_id,
                PromptPurchase.status == PurchaseStatus.completed,
            )
            .order_by(PromptPurchase.completed_at.desc().nullslast(), PromptPurchase.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
