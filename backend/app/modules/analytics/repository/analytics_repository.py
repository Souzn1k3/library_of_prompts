import uuid
from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AnalyticsEvent, ChannelSpendEntry, SessionAttribution, UserAttribution
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

    async def list_event_rows_with_dims(
        self,
        *,
        from_ts: datetime,
        to_ts: datetime | None = None,
        event_names: Sequence[str] | None = None,
        user_only: bool = False,
    ) -> Sequence[tuple[uuid.UUID | None, str, str, datetime, dict[str, Any], str | None, str | None, str | None, str | None, str | None]]:
        stmt = (
            select(
                AnalyticsEvent.user_id,
                AnalyticsEvent.session_id,
                AnalyticsEvent.event_name,
                AnalyticsEvent.occurred_at,
                AnalyticsEvent.metadata_json,
                AnalyticsEvent.utm_source,
                AnalyticsEvent.utm_medium,
                AnalyticsEvent.utm_campaign,
                AnalyticsEvent.ad_id,
                AnalyticsEvent.creative_id,
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

    async def get_session_attribution(self, *, session_id: str) -> SessionAttribution | None:
        result = await self._session.execute(
            select(SessionAttribution).where(SessionAttribution.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_session_attribution(self, row: SessionAttribution) -> SessionAttribution:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_session_attribution(self, row: SessionAttribution) -> SessionAttribution:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_user_attribution(self, *, user_id: uuid.UUID) -> UserAttribution | None:
        result = await self._session.execute(select(UserAttribution).where(UserAttribution.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_user_attribution(self, row: UserAttribution) -> UserAttribution:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_user_attribution(self, row: UserAttribution) -> UserAttribution:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_user_attributions(
        self,
        *,
        user_ids: Sequence[uuid.UUID] | None = None,
    ) -> Sequence[UserAttribution]:
        if user_ids is not None and len(user_ids) == 0:
            return []
        stmt = select(UserAttribution)
        if user_ids:
            stmt = stmt.where(UserAttribution.user_id.in_(list(user_ids)))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_channel_spend_by_dedupe_key(self, *, dedupe_key: str) -> ChannelSpendEntry | None:
        result = await self._session.execute(
            select(ChannelSpendEntry).where(ChannelSpendEntry.dedupe_key == dedupe_key)
        )
        return result.scalar_one_or_none()

    async def create_channel_spend(self, row: ChannelSpendEntry) -> ChannelSpendEntry:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def save_channel_spend(self, row: ChannelSpendEntry) -> ChannelSpendEntry:
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def list_channel_spend_rows(
        self,
        *,
        day_from: date,
        day_to: date,
    ) -> Sequence[ChannelSpendEntry]:
        stmt = (
            select(ChannelSpendEntry)
            .where(ChannelSpendEntry.spend_day >= day_from, ChannelSpendEntry.spend_day <= day_to)
            .order_by(ChannelSpendEntry.spend_day.asc(), ChannelSpendEntry.source.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
