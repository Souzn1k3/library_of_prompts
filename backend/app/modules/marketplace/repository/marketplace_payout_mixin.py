from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    MarketplacePayout,
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    PromptPurchase,
    PurchaseStatus,
)


class MarketplacePayoutMixin:
    async def list_settlement_ready_purchases(
        self,
        *,
        seller_user_id: uuid.UUID | None,
        now: datetime,
        limit: int = 200,
        for_update: bool = False,
    ) -> list[PromptPurchase]:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.status == PurchaseStatus.completed,
                PromptPurchase.settlement_status == MarketplaceSettlementStatus.pending,
                PromptPurchase.settlement_available_at.is_not(None),
                PromptPurchase.settlement_available_at <= now,
            )
            .order_by(PromptPurchase.settlement_available_at.asc(), PromptPurchase.created_at.asc())
            .limit(limit)
        )
        if seller_user_id is not None:
            stmt = stmt.where(PromptPurchase.seller_user_id == seller_user_id)
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_available_purchases_for_payout(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        limit: int = 200,
        for_update: bool = False,
    ) -> list[PromptPurchase]:
        stmt = (
            select(PromptPurchase)
            .where(
                PromptPurchase.seller_user_id == seller_user_id,
                PromptPurchase.status == PurchaseStatus.completed,
                PromptPurchase.settlement_status == MarketplaceSettlementStatus.available,
                PromptPurchase.payout_id.is_(None),
            )
            .order_by(PromptPurchase.completed_at.asc().nullslast(), PromptPurchase.created_at.asc())
            .limit(limit)
        )
        if currency_code.upper() == "LMN":
            stmt = stmt.where(PromptPurchase.seller_amount_lumens > 0)
        else:
            stmt = stmt.where(PromptPurchase.seller_amount_rub > 0)
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_payout(
        self,
        *,
        seller_user_id: uuid.UUID,
        currency_code: str,
        total_amount: int,
        purchase_count: int,
        notes: str | None = None,
    ) -> MarketplacePayout:
        payout = MarketplacePayout(
            seller_user_id=seller_user_id,
            currency_code=currency_code,
            status=MarketplacePayoutStatus.requested,
            total_amount=total_amount,
            purchase_count=purchase_count,
            notes=notes,
        )
        self._session.add(payout)
        await self._session.flush()
        await self._session.refresh(payout)
        return payout

    async def get_payout_by_id(self, payout_id: uuid.UUID, *, for_update: bool = False) -> MarketplacePayout | None:
        stmt = (
            select(MarketplacePayout)
            .options(selectinload(MarketplacePayout.purchases))
            .where(MarketplacePayout.id == payout_id)
            .limit(1)
        )
        stmt = self._maybe_for_update(stmt, for_update)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_payout(self, payout: MarketplacePayout) -> MarketplacePayout:
        await self._session.flush()
        await self._session.refresh(payout)
        return payout

    async def list_recent_payouts(self, seller_user_id: uuid.UUID, *, limit: int = 6) -> list[MarketplacePayout]:
        stmt = (
            select(MarketplacePayout)
            .where(MarketplacePayout.seller_user_id == seller_user_id)
            .order_by(MarketplacePayout.requested_at.desc(), MarketplacePayout.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
