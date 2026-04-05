from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from app.infrastructure.db.models import (
    AnalyticsEvent,
    CurrencyTransaction,
    MissionCompletionEvent,
    PurchaseStatus,
    User,
    UserCurrencyBalance,
    UserPurchase,
)


class EconomyKpiEventQueryMixin:
    async def list_users_created_between(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, datetime]]:
        rows = await self._session.execute(
            select(User.id, User.created_at).where(
                User.created_at >= start_at,
                User.created_at < end_at,
            )
        )
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_users_by_ids(self, *, user_ids: set[uuid.UUID]) -> list[tuple[uuid.UUID, datetime]]:
        if not user_ids:
            return []
        rows = await self._session.execute(
            select(User.id, User.created_at).where(User.id.in_(list(user_ids)))
        )
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_completed_purchases_between(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        user_ids: set[uuid.UUID] | None = None,
    ) -> list[tuple[uuid.UUID, datetime]]:
        stmt = select(UserPurchase.user_id, UserPurchase.created_at).where(
            UserPurchase.status == PurchaseStatus.completed,
            UserPurchase.created_at >= start_at,
            UserPurchase.created_at < end_at,
        )
        if user_ids is not None:
            if not user_ids:
                return []
            stmt = stmt.where(UserPurchase.user_id.in_(list(user_ids)))
        rows = await self._session.execute(stmt.order_by(UserPurchase.created_at.asc()))
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_first_two_purchases_for_users(
        self,
        *,
        user_ids: set[uuid.UUID],
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, int, datetime]]:
        if not user_ids:
            return []

        ranked = (
            select(
                UserPurchase.user_id.label("user_id"),
                UserPurchase.created_at.label("created_at"),
                func.row_number()
                .over(
                    partition_by=UserPurchase.user_id,
                    order_by=UserPurchase.created_at.asc(),
                )
                .label("purchase_rank"),
            )
            .where(
                UserPurchase.status == PurchaseStatus.completed,
                UserPurchase.user_id.in_(list(user_ids)),
                UserPurchase.created_at < end_at,
            )
            .subquery()
        )
        rows = await self._session.execute(
            select(
                ranked.c.user_id,
                ranked.c.purchase_rank,
                ranked.c.created_at,
            )
            .where(ranked.c.purchase_rank <= 2)
            .order_by(ranked.c.user_id.asc(), ranked.c.purchase_rank.asc())
        )
        return [
            (row[0], int(row[1]), row[2])
            for row in rows.all()
            if row[0] is not None and row[2] is not None
        ]

    async def list_currency_transactions_between(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, int, int, datetime]]:
        rows = await self._session.execute(
            select(
                CurrencyTransaction.user_id,
                CurrencyTransaction.amount,
                CurrencyTransaction.balance_after,
                CurrencyTransaction.created_at,
            ).where(
                CurrencyTransaction.created_at >= start_at,
                CurrencyTransaction.created_at < end_at,
            )
            .order_by(CurrencyTransaction.created_at.asc())
        )
        return [
            (row[0], int(row[1]), int(row[2]), row[3])
            for row in rows.all()
            if row[0] is not None and row[3] is not None
        ]

    async def list_balance_checkpoints_for_users(
        self,
        *,
        user_ids: set[uuid.UUID],
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, datetime, int]]:
        if not user_ids:
            return []
        rows = await self._session.execute(
            select(
                CurrencyTransaction.user_id,
                CurrencyTransaction.created_at,
                CurrencyTransaction.balance_after,
            )
            .where(
                CurrencyTransaction.user_id.in_(list(user_ids)),
                CurrencyTransaction.created_at < end_at,
            )
            .order_by(CurrencyTransaction.user_id.asc(), CurrencyTransaction.created_at.asc())
        )
        return [
            (row[0], row[1], int(row[2]))
            for row in rows.all()
            if row[0] is not None and row[1] is not None
        ]

    async def list_current_balances_for_users(self, *, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not user_ids:
            return {}
        rows = await self._session.execute(
            select(UserCurrencyBalance.user_id, UserCurrencyBalance.balance).where(
                UserCurrencyBalance.user_id.in_(list(user_ids))
            )
        )
        return {
            row[0]: int(row[1])
            for row in rows.all()
            if row[0] is not None and row[1] is not None
        }

    async def list_mission_completion_events_between(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, datetime]]:
        rows = await self._session.execute(
            select(
                MissionCompletionEvent.user_id,
                MissionCompletionEvent.created_at,
            ).where(
                MissionCompletionEvent.created_at >= start_at,
                MissionCompletionEvent.created_at < end_at,
            )
        )
        return [(row[0], row[1]) for row in rows.all() if row[0] is not None and row[1] is not None]

    async def list_analytics_events_between(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[tuple[uuid.UUID | None, str, str, dict[str, Any] | None, datetime]]:
        rows = await self._session.execute(
            select(
                AnalyticsEvent.user_id,
                AnalyticsEvent.event_name,
                AnalyticsEvent.context_page,
                AnalyticsEvent.metadata_json,
                AnalyticsEvent.occurred_at,
            ).where(
                AnalyticsEvent.occurred_at >= start_at,
                AnalyticsEvent.occurred_at < end_at,
            )
            .order_by(AnalyticsEvent.occurred_at.asc())
        )
        return [
            (
                row[0],
                str(row[1]),
                str(row[2]),
                row[3] if isinstance(row[3], dict) else None,
                row[4],
            )
            for row in rows.all()
            if row[4] is not None
        ]

    async def list_experiment_assignments_for_users(
        self,
        *,
        user_ids: set[uuid.UUID],
        end_at: datetime,
    ) -> list[tuple[uuid.UUID, datetime, dict[str, Any] | None]]:
        if not user_ids:
            return []
        rows = await self._session.execute(
            select(
                AnalyticsEvent.user_id,
                AnalyticsEvent.occurred_at,
                AnalyticsEvent.metadata_json,
            ).where(
                AnalyticsEvent.user_id.in_(list(user_ids)),
                AnalyticsEvent.event_name == "economy_experiment_assigned",
                AnalyticsEvent.occurred_at < end_at,
            )
            .order_by(AnalyticsEvent.user_id.asc(), AnalyticsEvent.occurred_at.asc())
        )
        return [
            (row[0], row[1], row[2] if isinstance(row[2], dict) else None)
            for row in rows.all()
            if row[0] is not None and row[1] is not None
        ]
