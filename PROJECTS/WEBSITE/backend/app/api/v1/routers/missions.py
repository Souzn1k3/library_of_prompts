from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.missions.model.mission import MissionCurrentRead, MissionListRead, MissionRead
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository

router = APIRouter(prefix="/missions", tags=["missions"])


def mission_service(session: AsyncSession = Depends(get_db)) -> MissionService:
    return MissionService(
        MissionRepository(session),
        OnboardingRepository(session),
        PromptRepository(session),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


@router.get("", response_model=MissionListRead)
async def list_missions(
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(mission_service),
) -> MissionListRead:
    return await svc.list_user_missions(current_user)


@router.get("/current", response_model=MissionCurrentRead)
async def current_mission(
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(mission_service),
) -> MissionCurrentRead:
    return await svc.current_user_mission(current_user)


@router.get("/{slug}", response_model=MissionRead)
async def mission_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(mission_service),
) -> MissionRead:
    return await svc.get_mission_by_slug(current_user, slug)


@router.post("/{slug}/confirm", response_model=MissionRead)
async def confirm_mission(
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: MissionService = Depends(mission_service),
) -> MissionRead:
    return await svc.confirm_manual_step(current_user, slug)
