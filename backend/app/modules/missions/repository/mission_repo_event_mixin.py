import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.infrastructure.db.models import MissionCompletionEvent


class MissionRepositoryEventMixin:
    async def add_completion_event(
        self,
        *,
        progress_id: uuid.UUID,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        mission_step_id: uuid.UUID | None,
        event_type: str,
        source_event_key: str,
        prompt_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        payload: dict[str, Any] | None,
        created_at: datetime,
    ) -> MissionCompletionEvent | None:
        stmt = (
            self._insert(MissionCompletionEvent)
            .values(
                progress_id=progress_id,
                user_id=user_id,
                mission_id=mission_id,
                mission_step_id=mission_step_id,
                event_type=event_type,
                source_event_key=source_event_key,
                prompt_id=prompt_id,
                lesson_id=lesson_id,
                payload=payload,
                created_at=created_at,
            )
            .on_conflict_do_nothing(index_elements=["source_event_key"])
        )
        if not self._is_sqlite():
            stmt = stmt.returning(MissionCompletionEvent.id)
            result = await self._session.execute(stmt)
            event_id = result.scalar_one_or_none()
            if event_id is None:
                return None
            row = await self._session.execute(
                select(MissionCompletionEvent).where(MissionCompletionEvent.id == event_id)
            )
            return row.scalar_one_or_none()

        result = await self._session.execute(stmt)
        if int(result.rowcount or 0) <= 0:
            return None
        row = await self._session.execute(
            select(MissionCompletionEvent).where(MissionCompletionEvent.source_event_key == source_event_key)
        )
        return row.scalar_one_or_none()
