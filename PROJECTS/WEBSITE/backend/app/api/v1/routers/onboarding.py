from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.cache import get_cache
from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.model.onboarding import (
    FirstWinCompleteRequest,
    OnboardingProfileRead,
    OnboardingProfileUpdate,
    OnboardingStarterPack,
)
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.onboarding.service.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def onboarding_service(session: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(
        OnboardingRepository(session),
        PromptRepository(session),
        LessonRepository(session),
    )


def mission_service(session: AsyncSession = Depends(get_db)) -> MissionService:
    return MissionService(
        MissionRepository(session),
        OnboardingRepository(session),
        PromptRepository(session),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


def contributor_service(session: AsyncSession = Depends(get_db)) -> ContributorService:
    return ContributorService(ContributorRepository(session), UserRepository(session))


@router.get("/profile", response_model=OnboardingProfileRead)
async def get_onboarding_profile(
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(onboarding_service),
) -> OnboardingProfileRead:
    return await svc.get_profile(current_user)


@router.put("/profile", response_model=OnboardingProfileRead)
async def update_onboarding_profile(
    body: OnboardingProfileUpdate,
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(onboarding_service),
    missions: MissionService = Depends(mission_service),
) -> OnboardingProfileRead:
    profile = await svc.upsert_profile(current_user, body)
    await missions.record_event(
        user=current_user,
        event_type="onboarding_completed",
        source_event_key=f"onboarding_completed:{current_user.id}",
    )
    await get_cache().bump("recommendations")
    return profile


@router.post("/skip", response_model=OnboardingProfileRead)
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(onboarding_service),
) -> OnboardingProfileRead:
    profile = await svc.skip(current_user)
    await get_cache().bump("recommendations")
    return profile


@router.get("/starter-pack", response_model=OnboardingStarterPack)
async def get_starter_pack(
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(onboarding_service),
) -> OnboardingStarterPack:
    return await svc.starter_pack(current_user)


@router.post("/first-win", response_model=OnboardingProfileRead)
async def complete_first_win(
    body: FirstWinCompleteRequest,
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(onboarding_service),
    missions: MissionService = Depends(mission_service),
    contributors: ContributorService = Depends(contributor_service),
) -> OnboardingProfileRead:
    profile = await svc.complete_first_win(current_user, body)
    await missions.record_event(
        user=current_user,
        event_type="onboarding_first_win_completed",
        prompt_id=body.prompt_id,
        source_event_key=f"onboarding_first_win_completed:{current_user.id}:{body.prompt_id}",
        payload={"action": body.action},
    )
    await contributors.refresh_prompt_quality(body.prompt_id)
    await get_cache().bump_many(("prompts", "recommendations"))
    return profile
