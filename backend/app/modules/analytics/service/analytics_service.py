import uuid
from datetime import datetime, timezone
import hashlib
from typing import Any

from app.core.errors import AppError
from app.core.logging import get_logger
from app.infrastructure.db.models import SessionAttribution, User, UserAttribution, UserRole
from app.modules.analytics.model.analytics import (
    AnalyticsAttribution,
    AnalyticsEventIn,
    AnalyticsEventName,
    AnalyticsEventRead,
    AttributionCaptureRead,
    AttributionCaptureWrite,
    AttributionTouchRead,
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

    def _normalize_attr(self, value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        return trimmed[:max_length]

    def _to_touch_read(
        self,
        *,
        utm_source: str | None,
        utm_medium: str | None,
        utm_campaign: str | None,
        referrer: str | None,
        seen_at: datetime,
    ) -> AttributionTouchRead:
        return AttributionTouchRead(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            referrer=referrer,
            seen_at=seen_at,
        )

    async def _upsert_attribution(
        self,
        *,
        session_id: str,
        attribution: AnalyticsAttribution,
        user: User | None,
        source: str,
    ) -> tuple[SessionAttribution, UserAttribution | None, bool]:
        now = datetime.now(timezone.utc)
        source_value = self._normalize_attr(attribution.utm_source, 120)
        medium_value = self._normalize_attr(attribution.utm_medium, 120)
        campaign_value = self._normalize_attr(attribution.utm_campaign, 160)
        referrer_value = self._normalize_attr(attribution.referrer, 500)

        session_row = await self._repo.get_session_attribution(session_id=session_id)
        if session_row is None:
            session_row = SessionAttribution(
                session_id=session_id,
                linked_user_id=user.id if user else None,
                first_utm_source=source_value,
                first_utm_medium=medium_value,
                first_utm_campaign=campaign_value,
                first_referrer=referrer_value,
                last_utm_source=source_value,
                last_utm_medium=medium_value,
                last_utm_campaign=campaign_value,
                last_referrer=referrer_value,
                first_seen_at=now,
                last_seen_at=now,
                created_at=now,
                updated_at=now,
            )
            session_row = await self._repo.create_session_attribution(session_row)
        else:
            if user is not None and session_row.linked_user_id is None:
                session_row.linked_user_id = user.id
            if source_value:
                session_row.last_utm_source = source_value
            if medium_value:
                session_row.last_utm_medium = medium_value
            if campaign_value:
                session_row.last_utm_campaign = campaign_value
            if referrer_value:
                session_row.last_referrer = referrer_value
            session_row.last_seen_at = now
            session_row.updated_at = now
            session_row = await self._repo.save_session_attribution(session_row)

        user_row: UserAttribution | None = None
        is_new_user_attribution = False
        if user is not None:
            user_row = await self._repo.get_user_attribution(user_id=user.id)
            if user_row is None:
                is_new_user_attribution = True
                user_row = UserAttribution(
                    user_id=user.id,
                    first_session_id=session_id,
                    last_session_id=session_id,
                    first_utm_source=session_row.first_utm_source,
                    first_utm_medium=session_row.first_utm_medium,
                    first_utm_campaign=session_row.first_utm_campaign,
                    first_referrer=session_row.first_referrer,
                    last_utm_source=session_row.last_utm_source,
                    last_utm_medium=session_row.last_utm_medium,
                    last_utm_campaign=session_row.last_utm_campaign,
                    last_referrer=session_row.last_referrer,
                    first_seen_at=session_row.first_seen_at,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                user_row = await self._repo.create_user_attribution(user_row)
            else:
                user_row.last_session_id = session_id
                if session_row.last_utm_source:
                    user_row.last_utm_source = session_row.last_utm_source
                if session_row.last_utm_medium:
                    user_row.last_utm_medium = session_row.last_utm_medium
                if session_row.last_utm_campaign:
                    user_row.last_utm_campaign = session_row.last_utm_campaign
                if session_row.last_referrer:
                    user_row.last_referrer = session_row.last_referrer
                user_row.last_seen_at = now
                user_row.updated_at = now
                user_row = await self._repo.save_user_attribution(user_row)

            if session_row.linked_user_id is None:
                session_row.linked_user_id = user.id
                session_row.updated_at = now
                session_row = await self._repo.save_session_attribution(session_row)

        await self.record_server_event(
            event_name=AnalyticsEventName.attribution_assigned,
            user_id=user.id if user else None,
            event_id=f"attribution_assigned:{session_id}:{now.date().isoformat()}",
            metadata={
                "session_id": session_id,
                "source": source,
                "utm_source": session_row.last_utm_source,
                "utm_medium": session_row.last_utm_medium,
                "utm_campaign": session_row.last_utm_campaign,
            },
            attribution=AnalyticsAttribution(
                utm_source=session_row.last_utm_source,
                utm_medium=session_row.last_utm_medium,
                utm_campaign=session_row.last_utm_campaign,
                referrer=session_row.last_referrer,
            ),
            session_id=session_id,
            context_page="/api/v1/analytics/attribution",
            context_feature="attribution",
        )
        return session_row, user_row, is_new_user_attribution

    async def ingest(
        self,
        events: list[AnalyticsEventIn],
        *,
        user: User | None,
    ) -> AnalyticsIngestResponse:
        accepted = len(events)
        if accepted == 0:
            return AnalyticsIngestResponse(accepted=0, ingested=0, duplicates=0)

        for event in events:
            if event.attribution is None:
                continue
            try:
                await self._upsert_attribution(
                    session_id=event.session_id,
                    attribution=event.attribution,
                    user=user,
                    source=event.source,
                )
            except Exception:
                log.exception("analytics_attribution_sync_failed", session_id=event.session_id)

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

    async def capture_attribution(
        self,
        *,
        body: AttributionCaptureWrite,
        user: User | None,
    ) -> AttributionCaptureRead:
        session_id = body.session_id.strip()
        if not session_id:
            raise AppError(
                code="invalid_session_id",
                message="Session id is required.",
                status_code=400,
            )

        session_row, user_row, is_new_user = await self._upsert_attribution(
            session_id=session_id,
            attribution=body.attribution,
            user=user,
            source=body.source,
        )

        if user is not None and is_new_user:
            await self.record_server_event(
                event_name=AnalyticsEventName.user_acquired,
                user_id=user.id,
                event_id=f"user_acquired:{user.id}",
                metadata={
                    "session_id": session_id,
                    "first_touch_source": user_row.first_utm_source if user_row else None,
                    "first_touch_campaign": user_row.first_utm_campaign if user_row else None,
                },
                attribution=AnalyticsAttribution(
                    utm_source=user_row.first_utm_source if user_row else None,
                    utm_medium=user_row.first_utm_medium if user_row else None,
                    utm_campaign=user_row.first_utm_campaign if user_row else None,
                    referrer=user_row.first_referrer if user_row else None,
                ),
                session_id=session_id,
                context_page="/api/v1/analytics/attribution",
                context_feature="acquisition",
            )

        return AttributionCaptureRead(
            session_id=session_row.session_id,
            user_id=user.id if user else None,
            first_touch=self._to_touch_read(
                utm_source=user_row.first_utm_source if user_row else session_row.first_utm_source,
                utm_medium=user_row.first_utm_medium if user_row else session_row.first_utm_medium,
                utm_campaign=user_row.first_utm_campaign if user_row else session_row.first_utm_campaign,
                referrer=user_row.first_referrer if user_row else session_row.first_referrer,
                seen_at=user_row.first_seen_at if user_row else session_row.first_seen_at,
            ),
            last_touch=self._to_touch_read(
                utm_source=user_row.last_utm_source if user_row else session_row.last_utm_source,
                utm_medium=user_row.last_utm_medium if user_row else session_row.last_utm_medium,
                utm_campaign=user_row.last_utm_campaign if user_row else session_row.last_utm_campaign,
                referrer=user_row.last_referrer if user_row else session_row.last_referrer,
                seen_at=user_row.last_seen_at if user_row else session_row.last_seen_at,
            ),
        )

    async def record_server_event(
        self,
        *,
        event_name: AnalyticsEventName,
        user_id: uuid.UUID | None,
        metadata: dict[str, Any] | None = None,
        attribution: AnalyticsAttribution | None = None,
        session_id: str = "server",
        context_page: str = "/server",
        context_feature: str = "server",
        event_id: str | None = None,
    ) -> None:
        event = AnalyticsEventIn(
            event_id=self._normalize_event_id(event_id or f"server_{event_name.value}_{uuid.uuid4().hex}"),
            event_name=event_name,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            context={"page": context_page, "feature": context_feature},
            metadata=metadata or {},
            attribution=attribution,
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

    async def get_user_last_touch_attribution(self, *, user_id: uuid.UUID) -> AnalyticsAttribution | None:
        row = await self._repo.get_user_attribution(user_id=user_id)
        if row is None:
            return None
        if not (row.last_utm_source or row.last_utm_medium or row.last_utm_campaign or row.last_referrer):
            return None
        return AnalyticsAttribution(
            utm_source=row.last_utm_source,
            utm_medium=row.last_utm_medium,
            utm_campaign=row.last_utm_campaign,
            referrer=row.last_referrer,
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
