from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.api.service_deps import get_mission_service, get_store_service
from app.api.support.rate_limit import RateLimitRule, enforce_request_rate_limits
from app.infrastructure.db.models import User
from app.modules.economy.model.store import PurchaseResult, StoreItemRead, StorePurchaseRequest
from app.modules.economy.service.store_service import StoreService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/store", tags=["store"])

_PURCHASE_LIMITS = (
    RateLimitRule(
        key_template="store:purchase:user:{user_id}",
        limit=30,
        window_seconds=10 * 60,
    ),
    RateLimitRule(
        key_template="store:purchase:ip:{ip}",
        limit=45,
        window_seconds=10 * 60,
    ),
)


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
    await enforce_request_rate_limits(
        request,
        _PURCHASE_LIMITS,
        values={"user_id": current_user.id},
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
