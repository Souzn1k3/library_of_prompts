import uuid
from datetime import datetime, timezone
import hashlib
from typing import Any

from app.core.errors import AppError
from app.core.logging import get_logger
from app.infrastructure.db.models import User, UserRole
from app.modules.analytics.model.analytics import (
    AnalyticsEventIn,
    AnalyticsEventName,
    AnalyticsEventRead,
    AnalyticsIngestResponse,
)
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository

log = get_logger(__name__)


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository) -> None:
        self._repo = repo

    def _event_row(self, event: AnalyticsEventIn, *, user_id: uuid.UUID | None) -> dict[str, Any]:
        attribution = event.attribution
        return {
            "event_id": event.event_id,
            "event_name": event.event_name.value,
            "user_id": user_id,
            "session_id": event.session_id,
            "source": event.source,
            "context_page": event.context.page,
            "context_feature": event.context.feature,
            "utm_source": attribution.utm_source if attribution else None,
            "utm_medium": attribution.utm_medium if attribution else None,
            "utm_campaign": attribution.utm_campaign if attribution else None,
            "utm_term": attribution.utm_term if attribution else None,
            "utm_content": attribution.utm_content if attribution else None,
            "referrer": attribution.referrer if attribution else None,
            "metadata_json": event.metadata,
            "occurred_at": event.timestamp,
            "ingested_at": datetime.now(timezone.utc),
        }

    def _normalize_event_id(self, event_id: str) -> str:
        trimmed = event_id.strip()
        if len(trimmed) <= 80:
            return trimmed
        digest = hashlib.sha1(trimmed.encode("utf-8")).hexdigest()[:12]
        prefix = trimmed[:67].rstrip(":_-")
        return f"{prefix}:{digest}"[:80]

    async def ingest(
        self,
        events: list[AnalyticsEventIn],
        *,
        user: User | None,
    ) -> AnalyticsIngestResponse:
        accepted = len(events)
        if accepted == 0:
            return AnalyticsIngestResponse(accepted=0, ingested=0, duplicates=0)

        rows = [self._event_row(event, user_id=user.id if user else None) for event in events]
        try:
            ingested = await self._repo.ingest_rows(rows)
        except Exception:
            log.exception(
                "analytics_ingest_failed",
                observability_event="analytics_ingest_failed",
                accepted=accepted,
            )
            raise AppError(
                code="analytics_ingest_failed",
                message="We couldn't save activity data right now.",
                status_code=500,
            ) from None

        duplicates = max(accepted - ingested, 0)
        if duplicates > 0:
            log.info("analytics_duplicates", accepted=accepted, ingested=ingested, duplicates=duplicates)

        return AnalyticsIngestResponse(
            accepted=accepted,
            ingested=ingested,
            duplicates=duplicates,
        )

    async def record_server_event(
        self,
        *,
        event_name: AnalyticsEventName,
        user_id: uuid.UUID | None,
        metadata: dict[str, Any] | None = None,
        context_page: str = "/server",
        context_feature: str = "server",
        event_id: str | None = None,
    ) -> None:
        event = AnalyticsEventIn(
            event_id=self._normalize_event_id(event_id or f"server_{event_name.value}_{uuid.uuid4().hex}"),
            event_name=event_name,
            session_id="server",
            timestamp=datetime.now(timezone.utc),
            context={"page": context_page, "feature": context_feature},
            metadata=metadata or {},
            source="server",
        )
        try:
            await self._repo.ingest_rows([self._event_row(event, user_id=user_id)])
        except Exception:
            log.exception(
                "analytics_server_event_failed",
                event_name=event_name.value,
                event_id=event.event_id,
            )

    async def recent_events(
        self,
        *,
        limit: int,
        event_name: AnalyticsEventName | None,
        from_ts: datetime | None,
        user: User | None,
    ) -> list[AnalyticsEventRead]:
        if user is None or user.role != UserRole.admin:
            raise AppError(
                code="insufficient_permissions",
                message="You don't have access to this action.",
                status_code=403,
                message_key="errors.insufficient_permissions",
            )

        rows = await self._repo.list_recent(limit=limit, event_name=event_name, from_ts=from_ts)
        return [AnalyticsEventRead.model_validate(row) for row in rows]
