from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.economy.model.wallet import WalletRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.economy.service.wallet_service import WalletService
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService

router = APIRouter(prefix="/wallet", tags=["wallet"])


def wallet_service(session: AsyncSession = Depends(get_db)) -> WalletService:
    return WalletService(WalletRepository(session), StoreRepository(session))


def mission_service(session: AsyncSession = Depends(get_db)) -> MissionService:
    return MissionService(
        MissionRepository(session),
        OnboardingRepository(session),
        PromptRepository(session),
        wallet_repo=WalletRepository(session),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


@router.get("", response_model=WalletRead)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    svc: WalletService = Depends(wallet_service),
) -> WalletRead:
    await svc.ensure_wallet(current_user.id)
    return await svc.get_wallet(current_user, limit=25)


@router.post("/check-in", response_model=WalletRead)
async def daily_checkin(
    current_user: User = Depends(get_current_user),
    svc: WalletService = Depends(wallet_service),
    missions: MissionService = Depends(mission_service),
) -> WalletRead:
    today_key = datetime.now(timezone.utc).date().isoformat()
    await missions.record_event(
        user=current_user,
        event_type="daily_checkin",
        source_event_key=f"daily_checkin:{current_user.id}:{today_key}",
    )
    await svc.daily_checkin_bonus(current_user.id)
    return await svc.get_wallet(current_user, limit=25)
