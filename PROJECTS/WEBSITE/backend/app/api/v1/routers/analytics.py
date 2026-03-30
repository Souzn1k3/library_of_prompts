from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import get_optional_user
from app.api.service_deps import get_analytics_service
from app.core.rate_limit import enforce_rate_limit, resolve_rate_limit_ip
from app.infrastructure.db.models import User
from app.modules.analytics.model.analytics import (
    AnalyticsEventName,
    AnalyticsEventRead,
    AnalyticsIngestPayload,
    AnalyticsIngestResponse,
)
from app.modules.analytics.service.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", response_model=AnalyticsIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    request: Request,
    body: AnalyticsIngestPayload,
    viewer: User | None = Depends(get_optional_user),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsIngestResponse:
    ip = resolve_rate_limit_ip(request)
    principal = str(viewer.id) if viewer is not None else ip
    await enforce_rate_limit(
        key=f"analytics:ingest:{principal}",
        limit=180,
        window_seconds=5 * 60,
    )
    events = body.normalized_events()
    return await svc.ingest(events, user=viewer)


@router.get("/events/recent", response_model=list[AnalyticsEventRead])
async def recent_events(
    limit: int = Query(default=100, ge=1, le=500),
    event_name: AnalyticsEventName | None = Query(default=None),
    hours: int | None = Query(default=None, ge=1, le=24 * 30),
    viewer: User | None = Depends(get_optional_user),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> list[AnalyticsEventRead]:
    from_ts = datetime.now(timezone.utc) - timedelta(hours=hours) if hours else None
    return await svc.recent_events(
        limit=limit,
        event_name=event_name,
        from_ts=from_ts,
        user=viewer,
    )
