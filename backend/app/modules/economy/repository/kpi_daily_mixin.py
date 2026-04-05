from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select

from app.infrastructure.db.models import EconomyDailyKpi


class EconomyKpiDailyMixin:
    async def upsert_daily_kpis(self, *, rows: Sequence[dict[str, Any]]) -> int:
        if not rows:
            return 0
        now = datetime.now(timezone.utc)
        payloads = []
        for row in rows:
            payloads.append(
                {
                    "id": uuid.uuid4(),
                    "created_at": now,
                    "updated_at": now,
                    **row,
                }
            )

        stmt = self._insert(EconomyDailyKpi).values(payloads)
        update_columns = {
            "active_users": stmt.excluded.active_users,
            "new_users": stmt.excluded.new_users,
            "first_purchase_users": stmt.excluded.first_purchase_users,
            "second_purchase_48h_users": stmt.excluded.second_purchase_48h_users,
            "second_purchase_48h_rate": stmt.excluded.second_purchase_48h_rate,
            "d1_retention_rate": stmt.excluded.d1_retention_rate,
            "d7_retention_rate": stmt.excluded.d7_retention_rate,
            "lmn_earned": stmt.excluded.lmn_earned,
            "lmn_spent": stmt.excluded.lmn_spent,
            "lmn_spent_earned_ratio": stmt.excluded.lmn_spent_earned_ratio,
            "avg_balance": stmt.excluded.avg_balance,
            "median_balance": stmt.excluded.median_balance,
            "store_views": stmt.excluded.store_views,
            "store_purchases": stmt.excluded.store_purchases,
            "store_conversion_rate": stmt.excluded.store_conversion_rate,
            "wallet_views": stmt.excluded.wallet_views,
            "mission_completions": stmt.excluded.mission_completions,
            "avg_time_to_first_purchase_hours": stmt.excluded.avg_time_to_first_purchase_hours,
            "avg_time_to_second_purchase_hours": stmt.excluded.avg_time_to_second_purchase_hours,
            "updated_at": now,
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["date", "experiment_name", "cohort"],
            set_=update_columns,
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def list_kpis(
        self,
        *,
        start_date: date,
        end_date: date,
        experiment_name: str | None = None,
    ) -> list[EconomyDailyKpi]:
        stmt = select(EconomyDailyKpi).where(
            EconomyDailyKpi.date >= start_date,
            EconomyDailyKpi.date <= end_date,
        )
        if experiment_name:
            stmt = stmt.where(EconomyDailyKpi.experiment_name == experiment_name)
        stmt = stmt.order_by(
            EconomyDailyKpi.date.asc(),
            EconomyDailyKpi.experiment_name.asc(),
            EconomyDailyKpi.cohort.asc(),
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())
