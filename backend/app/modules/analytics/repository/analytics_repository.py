import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AnalyticsEvent
from app.modules.analytics.model.analytics import AnalyticsEventName


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    async def ingest_rows(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        insert_fn = sqlite_insert if self._is_sqlite() else pg_insert
        stmt = insert_fn(AnalyticsEvent).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["event_id"])

        if not self._is_sqlite():
            stmt = stmt.returning(AnalyticsEvent.id)
            result = await self._session.execute(stmt)
            inserted_ids = result.scalars().all()
            return len(inserted_ids)

        result = await self._session.execute(stmt)
        # sqlite rowcount is reliable for INSERT ... ON CONFLICT DO NOTHING
        return max(int(result.rowcount or 0), 0)

    async def list_recent(
        self,
        *,
        limit: int = 100,
        event_name: AnalyticsEventName | None = None,
        user_id: uuid.UUID | None = None,
        from_ts: datetime | None = None,
    ) -> Sequence[AnalyticsEvent]:
        stmt = select(AnalyticsEvent)
        if event_name is not None:
            stmt = stmt.where(AnalyticsEvent.event_name == event_name.value)
        if user_id is not None:
            stmt = stmt.where(AnalyticsEvent.user_id == user_id)
        if from_ts is not None:
            stmt = stmt.where(AnalyticsEvent.occurred_at >= from_ts)
        stmt = stmt.order_by(AnalyticsEvent.occurred_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_recent_for_user(
        self,
        *,
        user_id: uuid.UUID,
        event_names: Sequence[AnalyticsEventName],
        limit: int = 100,
        from_ts: datetime | None = None,
    ) -> Sequence[AnalyticsEvent]:
        if not event_names:
            return []
        stmt = select(AnalyticsEvent).where(
            AnalyticsEvent.user_id == user_id,
            AnalyticsEvent.event_name.in_([event_name.value for event_name in event_names]),
        )
        if from_ts is not None:
            stmt = stmt.where(AnalyticsEvent.occurred_at >= from_ts)
        stmt = stmt.order_by(AnalyticsEvent.occurred_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_event_rows(
        self,
        *,
        from_ts: datetime,
        to_ts: datetime | None = None,
        event_names: Sequence[str] | None = None,
        user_only: bool = False,
    ) -> Sequence[tuple[uuid.UUID | None, str, str, datetime, dict[str, Any]]]:
        stmt = (
            select(
                AnalyticsEvent.user_id,
                AnalyticsEvent.session_id,
                AnalyticsEvent.event_name,
                AnalyticsEvent.occurred_at,
                AnalyticsEvent.metadata_json,
            )
            .where(AnalyticsEvent.occurred_at >= from_ts)
            .order_by(AnalyticsEvent.occurred_at.asc())
        )
        if to_ts is not None:
            stmt = stmt.where(AnalyticsEvent.occurred_at < to_ts)
        if event_names:
            stmt = stmt.where(AnalyticsEvent.event_name.in_(list(event_names)))
        if user_only:
            stmt = stmt.where(AnalyticsEvent.user_id.is_not(None))
        result = await self._session.execute(stmt)
        return result.all()

    async def count_distinct_users(
        self,
        *,
        from_ts: datetime,
        to_ts: datetime | None = None,
        event_names: Sequence[str] | None = None,
    ) -> int:
        stmt = select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
            AnalyticsEvent.occurred_at >= from_ts,
            AnalyticsEvent.user_id.is_not(None),
        )
        if to_ts is not None:
            stmt = stmt.where(AnalyticsEvent.occurred_at < to_ts)
        if event_names:
            stmt = stmt.where(AnalyticsEvent.event_name.in_(list(event_names)))
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def count_distinct_sessions(
        self,
        *,
        from_ts: datetime,
        to_ts: datetime | None = None,
        event_names: Sequence[str] | None = None,
    ) -> int:
        stmt = select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.occurred_at >= from_ts,
        )
        if to_ts is not None:
            stmt = stmt.where(AnalyticsEvent.occurred_at < to_ts)
        if event_names:
            stmt = stmt.where(AnalyticsEvent.event_name.in_(list(event_names)))
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)
