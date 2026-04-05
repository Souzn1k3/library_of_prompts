from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


class EconomyKpiBaseMixin:
    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model: Any):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    async def try_acquire_aggregation_lock(self, *, lock_key: int) -> bool:
        bind = self._session.bind
        if bind is None or bind.dialect.name != "postgresql":
            return True
        row = await self._session.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": int(lock_key)},
        )
        return bool(row.scalar_one())
