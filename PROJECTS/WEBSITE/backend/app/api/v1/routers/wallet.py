from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.service_deps import get_mission_service, get_wallet_service
from app.infrastructure.db.models import User
from app.modules.economy.model.wallet import WalletRead
from app.modules.economy.service.wallet_service import WalletService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletRead)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    svc: WalletService = Depends(get_wallet_service),
) -> WalletRead:
    await svc.ensure_wallet(current_user.id)
    return await svc.get_wallet(current_user, limit=25)


@router.post("/check-in", response_model=WalletRead)
async def daily_checkin(
    current_user: User = Depends(get_current_user),
    svc: WalletService = Depends(get_wallet_service),
    missions: MissionService = Depends(get_mission_service),
) -> WalletRead:
    today_key = datetime.now(timezone.utc).date().isoformat()
    await missions.record_event(
        user=current_user,
        event_type="daily_checkin",
        source_event_key=f"daily_checkin:{current_user.id}:{today_key}",
    )
    await svc.daily_checkin_bonus(current_user.id)
    return await svc.get_wallet(current_user, limit=25)
