from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import get_optional_user
from app.api.service_deps import get_analytics_service, get_growth_ops_service, get_revenue_ops_service
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.infrastructure.db.models import User
from app.modules.analytics.model.analytics import (
    AnalyticsEventName,
    AnalyticsEventRead,
    AttributionCaptureRead,
    AttributionCaptureWrite,
    AnalyticsIngestPayload,
    AnalyticsIngestResponse,
)
from app.modules.analytics.model.growth import GrowthDashboardRead, GrowthRuntimeRead
from app.modules.analytics.model.revenue import RevenueDashboardRead
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.analytics.service.growth_ops_service import GrowthOpsService
from app.modules.analytics.service.revenue_ops_service import RevenueOpsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

_INGEST_USER_LIMITS = (
    RateLimitRule(
        key_template="analytics:ingest:user:{user_id}",
        limit=180,
        window_seconds=5 * 60,
    ),
)

_INGEST_IP_LIMITS = (
    RateLimitRule(
        key_template="analytics:ingest:ip:{ip}",
        limit=180,
        window_seconds=5 * 60,
    ),
)

_GROWTH_RUNTIME_USER_LIMITS = (
    RateLimitRule(
        key_template="analytics:growth-runtime:user:{user_id}",
        limit=240,
        window_seconds=5 * 60,
    ),
)

_GROWTH_RUNTIME_IP_LIMITS = (
    RateLimitRule(
        key_template="analytics:growth-runtime:ip:{ip}",
        limit=180,
        window_seconds=5 * 60,
    ),
)


@router.post("/events", response_model=AnalyticsIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    request: Request,
    body: AnalyticsIngestPayload,
    viewer: User | None = Depends(get_optional_user),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsIngestResponse:
    if viewer is None:
        await enforce_request_rate_limits(request, _INGEST_IP_LIMITS)
    else:
        await enforce_request_rate_limits(request, _INGEST_USER_LIMITS, values={"user_id": viewer.id})
    events = body.normalized_events()
    return await svc.ingest(events, user=viewer)


@router.post("/attribution", response_model=AttributionCaptureRead)
async def capture_attribution(
    request: Request,
    body: AttributionCaptureWrite,
    viewer: User | None = Depends(get_optional_user),
    svc: AnalyticsService = Depends(get_analytics_service),
) -> AttributionCaptureRead:
    if viewer is None:
        await enforce_request_rate_limits(request, _INGEST_IP_LIMITS)
    else:
        await enforce_request_rate_limits(request, _INGEST_USER_LIMITS, values={"user_id": viewer.id})
    return await svc.capture_attribution(body=body, user=viewer)


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


@router.get("/growth/runtime", response_model=GrowthRuntimeRead)
async def growth_runtime(
    request: Request,
    session_id: str = Query(default="", min_length=0, max_length=120),
    page: str = Query(default="/", min_length=1, max_length=260),
    feature: str = Query(default="growth_runtime", min_length=1, max_length=120),
    viewer: User | None = Depends(get_optional_user),
    svc: GrowthOpsService = Depends(get_growth_ops_service),
) -> GrowthRuntimeRead:
    if viewer is None:
        await enforce_request_rate_limits(request, _GROWTH_RUNTIME_IP_LIMITS)
    else:
        await enforce_request_rate_limits(request, _GROWTH_RUNTIME_USER_LIMITS, values={"user_id": viewer.id})
    effective_session_id = session_id.strip() or "guest"
    return await svc.runtime_decisions(
        user=viewer,
        session_id=effective_session_id,
        page=page,
        feature=feature,
    )


@router.get("/growth/dashboard", response_model=GrowthDashboardRead)
async def growth_dashboard(
    window_days: int = Query(default=28, ge=7, le=90),
    viewer: User | None = Depends(get_optional_user),
    svc: GrowthOpsService = Depends(get_growth_ops_service),
) -> GrowthDashboardRead:
    return await svc.dashboard(
        user=viewer,
        window_days=window_days,
    )


@router.get("/revenue/dashboard", response_model=RevenueDashboardRead)
async def revenue_dashboard(
    window_days: int = Query(default=30, ge=7, le=90),
    viewer: User | None = Depends(get_optional_user),
    svc: RevenueOpsService = Depends(get_revenue_ops_service),
) -> RevenueDashboardRead:
    return await svc.dashboard(
        user=viewer,
        window_days=window_days,
    )
