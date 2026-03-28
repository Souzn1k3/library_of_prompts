from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.economy.model.store import PurchaseResult, StoreItemRead, StorePurchaseRequest
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.store_service import StoreService

router = APIRouter(prefix="/store", tags=["store"])


def store_service(session: AsyncSession = Depends(get_db)) -> StoreService:
    wallet_repo = WalletRepository(session)
    return StoreService(StoreRepository(session), wallet_repo)


@router.get("", response_model=list[StoreItemRead])
async def list_items(
    current_user: User = Depends(get_current_user),
    svc: StoreService = Depends(store_service),
) -> list[StoreItemRead]:
    return await svc.list_items(current_user)


@router.post("/{slug}/purchase", response_model=PurchaseResult)
async def purchase_item(
    slug: str,
    body: StorePurchaseRequest | None = None,
    current_user: User = Depends(get_current_user),
    svc: StoreService = Depends(store_service),
) -> PurchaseResult:
    return await svc.purchase(
        user=current_user,
        item_slug=slug,
        client_token=body.client_token if body is not None else None,
    )
