import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.api.service_deps import (
    get_economy_insights_service,
    get_economy_kpi_service,
    get_marketplace_service,
)
from app.core.errors import NotFoundError
from app.infrastructure.db.models import User
from app.modules.economy.model.insights import EconomyExperimentKpiRead, EconomyTuningRead
from app.modules.economy.model.kpis import EconomyKpiSummaryRead
from app.infrastructure.db.session import get_db
from app.modules.identity.model.admin import AdminTierUpdate
from app.modules.identity.model.user import UserRead
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.marketplace.model.marketplace import MarketplacePayoutFinalizeWrite, MarketplacePayoutRead
from app.modules.marketplace.service.marketplace_service import MarketplaceService
from app.modules.economy.service.insights_service import EconomyInsightsService
from app.modules.economy.service.kpi_service import EconomyKpiService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/users/{user_id}/tier", response_model=UserRead)
async def set_user_tier(
    user_id: uuid.UUID,
    body: AdminTierUpdate,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    repo = UserRepository(session)
    user = await repo.set_plan_tier(user_id, body.plan_tier)
    if user is None:
        raise NotFoundError("user", str(user_id))
    return UserRead.model_validate(user)


@router.post("/marketplace/payouts/{payout_id}/processing", response_model=MarketplacePayoutRead)
async def mark_marketplace_payout_processing(
    payout_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplacePayoutRead:
    return await svc.mark_payout_processing(payout_id=payout_id)


@router.post("/marketplace/payouts/{payout_id}/finalize", response_model=MarketplacePayoutRead)
async def finalize_marketplace_payout(
    payout_id: uuid.UUID,
    body: MarketplacePayoutFinalizeWrite,
    _admin: User = Depends(require_admin),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplacePayoutRead:
    return await svc.finalize_payout(payout_id=payout_id, reference=body.reference)


@router.post("/marketplace/payouts/{payout_id}/fail", response_model=MarketplacePayoutRead)
async def fail_marketplace_payout(
    payout_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplacePayoutRead:
    return await svc.fail_payout(payout_id=payout_id)


@router.post("/marketplace/payouts/{payout_id}/cancel", response_model=MarketplacePayoutRead)
async def cancel_marketplace_payout(
    payout_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    svc: MarketplaceService = Depends(get_marketplace_service),
) -> MarketplacePayoutRead:
    return await svc.cancel_payout(payout_id=payout_id)


@router.get("/economy/experiment-kpis", response_model=EconomyExperimentKpiRead)
async def economy_experiment_kpis(
    window_days: int = Query(default=14, ge=7, le=90),
    _admin: User = Depends(require_admin),
    svc: EconomyInsightsService = Depends(get_economy_insights_service),
) -> EconomyExperimentKpiRead:
    return await svc.experiment_kpis(window_days=window_days)


@router.get("/economy/tuning", response_model=EconomyTuningRead)
async def economy_weekly_tuning(
    window_days: int = Query(default=7, ge=7, le=28),
    _admin: User = Depends(require_admin),
    svc: EconomyInsightsService = Depends(get_economy_insights_service),
) -> EconomyTuningRead:
    return await svc.weekly_tuning(window_days=window_days)


@router.get("/economy/kpis/summary", response_model=EconomyKpiSummaryRead)
async def economy_kpi_summary(
    _admin: User = Depends(require_admin),
    svc: EconomyKpiService = Depends(get_economy_kpi_service),
) -> EconomyKpiSummaryRead:
    return await svc.summary()


@router.get("/economy/kpis/export")
async def economy_kpi_export_csv(
    format: Literal["csv"] = Query(default="csv"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    _admin: User = Depends(require_admin),
    svc: EconomyKpiService = Depends(get_economy_kpi_service),
) -> Response:
    _ = format
    filename, content = await svc.export_csv(start_date=start_date, end_date=end_date)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
