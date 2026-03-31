from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.service_deps import get_contributor_service, get_mission_service, get_onboarding_service, get_store_service
from app.core.cache import get_cache
from app.infrastructure.db.models import User
from app.modules.economy.service.store_service import StoreService
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.model.onboarding import (
    FirstWinCompleteRequest,
    OnboardingProfileRead,
    OnboardingFirstWinResult,
    OnboardingProfileUpdate,
    OnboardingStarterPack,
)
from app.modules.onboarding.service.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/profile", response_model=OnboardingProfileRead)
async def get_onboarding_profile(
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingProfileRead:
    return await svc.get_profile(current_user)


@router.put("/profile", response_model=OnboardingProfileRead)
async def update_onboarding_profile(
    body: OnboardingProfileUpdate,
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(get_onboarding_service),
    missions: MissionService = Depends(get_mission_service),
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
    svc: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingProfileRead:
    profile = await svc.skip(current_user)
    await get_cache().bump("recommendations")
    return profile


@router.get("/starter-pack", response_model=OnboardingStarterPack)
async def get_starter_pack(
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStarterPack:
    return await svc.starter_pack(current_user)


@router.post("/first-win", response_model=OnboardingFirstWinResult)
async def complete_first_win(
    body: FirstWinCompleteRequest,
    current_user: User = Depends(get_current_user),
    svc: OnboardingService = Depends(get_onboarding_service),
    missions: MissionService = Depends(get_mission_service),
    contributors: ContributorService = Depends(get_contributor_service),
    store: StoreService = Depends(get_store_service),
) -> OnboardingFirstWinResult:
    previous_balance = (await store.wallet(current_user)).balance
    profile = await svc.complete_first_win(current_user, body)
    today_key = datetime.now(timezone.utc).date().isoformat()
    completed = await missions.record_event(
        user=current_user,
        event_type="onboarding_first_win_completed",
        prompt_id=body.prompt_id,
        source_event_key=f"onboarding_first_win_completed:{current_user.id}:{body.prompt_id}",
        payload={"action": body.action},
    )
    completed.extend(
        await missions.record_event(
            user=current_user,
            event_type="streak_activity",
            prompt_id=body.prompt_id,
            source_event_key=f"streak_activity:{current_user.id}:{today_key}",
            payload={"source": "onboarding_first_win_completed", "action": body.action},
        )
    )
    await contributors.refresh_prompt_quality(body.prompt_id)
    await get_cache().bump_many(("prompts", "recommendations"))
    economy = await store.build_action_feedback(
        current_user,
        previous_balance=previous_balance,
        completed_mission_slugs=list(dict.fromkeys(completed)),
    )
    return OnboardingFirstWinResult(profile=profile, economy=economy)
