from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.api.service_deps import get_mission_service, get_store_service
from app.core.rate_limit import enforce_rate_limit, resolve_rate_limit_ip
from app.infrastructure.db.models import User
from app.modules.economy.model.store import PurchaseResult, StoreItemRead, StorePurchaseRequest
from app.modules.economy.service.store_service import StoreService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/store", tags=["store"])


@router.get("", response_model=list[StoreItemRead])
async def list_items(
    current_user: User = Depends(get_current_user),
    svc: StoreService = Depends(get_store_service),
) -> list[StoreItemRead]:
    return await svc.list_items(current_user)


@router.post("/{slug}/purchase", response_model=PurchaseResult)
async def purchase_item(
    request: Request,
    slug: str,
    body: StorePurchaseRequest | None = None,
    current_user: User = Depends(get_current_user),
    svc: StoreService = Depends(get_store_service),
    missions: MissionService = Depends(get_mission_service),
) -> PurchaseResult:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(
        key=f"store:purchase:user:{current_user.id}",
        limit=30,
        window_seconds=10 * 60,
    )
    await enforce_rate_limit(
        key=f"store:purchase:ip:{ip}",
        limit=45,
        window_seconds=10 * 60,
    )
    result = await svc.purchase(
        user=current_user,
        item_slug=slug,
        client_token=body.client_token if body is not None else None,
    )
    await missions.record_event(
        user=current_user,
        event_type="store_purchase",
        source_event_key=f"store_purchase:{current_user.id}:{result.purchase.id}",
        payload={"item_slug": slug, "purchase_id": str(result.purchase.id)},
    )
    return result
