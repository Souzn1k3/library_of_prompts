from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    AnalyticsEvent,
    CurrencyTransaction,
    MissionCompletionEvent,
    PurchaseStatus,
    UserCurrencyBalance,
    UserPurchase,
)


class EconomyInsightsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_purchases(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, datetime]]:
        stmt = select(UserPurchase.user_id, UserPurchase.created_at).where(
            UserPurchase.created_at >= start_at,
            UserPurchase.created_at < end_at,
            UserPurchase.status == PurchaseStatus.completed,
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(UserPurchase.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt.order_by(UserPurchase.created_at.asc()))
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_mission_events(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, datetime]]:
        stmt = select(MissionCompletionEvent.user_id, MissionCompletionEvent.created_at).where(
            MissionCompletionEvent.created_at >= start_at,
            MissionCompletionEvent.created_at < end_at,
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(MissionCompletionEvent.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt.order_by(MissionCompletionEvent.created_at.asc()))
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_currency_transactions(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, int, str, datetime]]:
        stmt = select(
            CurrencyTransaction.user_id,
            CurrencyTransaction.amount,
            CurrencyTransaction.reason,
            CurrencyTransaction.created_at,
        ).where(
            CurrencyTransaction.created_at >= start_at,
            CurrencyTransaction.created_at < end_at,
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(CurrencyTransaction.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt.order_by(CurrencyTransaction.created_at.asc()))
        return [
            (row[0], int(row[1]), row[2].value if hasattr(row[2], "value") else str(row[2]), row[3])
            for row in rows.all()
            if row[0] is not None and row[3] is not None
        ]

    async def list_wallet_rows(
        self,
        *,
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, int, int, int, int]]:
        stmt = select(
            UserCurrencyBalance.user_id,
            UserCurrencyBalance.current_streak,
            UserCurrencyBalance.balance,
            UserCurrencyBalance.rank_level,
            UserCurrencyBalance.total_spent,
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(UserCurrencyBalance.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt)
        return [
            (row[0], int(row[1]), int(row[2]), int(row[3]), int(row[4]))
            for row in rows.all()
            if row[0] is not None
        ]

    async def list_analytics_events(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        event_names: Sequence[str],
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID | None, str, dict[str, Any] | None, datetime]]:
        if not event_names:
            return []
        stmt = select(
            AnalyticsEvent.user_id,
            AnalyticsEvent.event_name,
            AnalyticsEvent.metadata_json,
            AnalyticsEvent.occurred_at,
        ).where(
            AnalyticsEvent.occurred_at >= start_at,
            AnalyticsEvent.occurred_at < end_at,
            AnalyticsEvent.event_name.in_(list(event_names)),
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(AnalyticsEvent.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt.order_by(AnalyticsEvent.occurred_at.asc()))
        return [
            (row[0], str(row[1]), row[2] if isinstance(row[2], dict) else None, row[3])
            for row in rows.all()
            if row[3] is not None
        ]
