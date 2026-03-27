import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.cache import get_cache
from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.model.prompt import AuthorPromptRow, PromptListItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.identity.model.user import UserRead
from app.modules.identity.model.user_update import UserUpdateMe
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.saved_prompt_service import SavedPromptService
from app.modules.identity.service.user_service import UserService
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository

router = APIRouter(prefix="/users", tags=["users"])


def user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


def saved_prompt_service(session: AsyncSession = Depends(get_db)) -> SavedPromptService:
    return SavedPromptService(
        SavedPromptRepository(session),
        PromptRepository(session),
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


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    svc: UserService = Depends(user_service),
) -> UserRead:
    return await svc.update_me(current_user.id, body)


@router.get("/me/submissions", response_model=list[AuthorPromptRow])
async def my_submissions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    contributors: ContributorService = Depends(contributor_service),
) -> list[AuthorPromptRow]:
    repo = PromptRepository(session)
    rows = await repo.list_by_author(current_user.id, skip=0, limit=100)
    return [
        AuthorPromptRow(
            id=row.id,
            slug=row.slug,
            title=row.title,
            status=row.status,
            moderation_state=row.moderation_state,
            moderation_notes=row.moderation_notes,
            moderated_at=row.moderated_at,
            auto_approved=row.auto_approved,
            feedback_hints=contributors.feedback_hints(row.moderation_notes),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/me/saved-prompts", response_model=list[PromptListItem])
async def list_saved_prompts(
    current_user: User = Depends(get_current_user),
    svc: SavedPromptService = Depends(saved_prompt_service),
) -> list[PromptListItem]:
    return await svc.list_saved(current_user.id)


@router.post("/me/saved-prompts/{prompt_id}", status_code=204)
async def save_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: SavedPromptService = Depends(saved_prompt_service),
    missions: MissionService = Depends(mission_service),
    contributors: ContributorService = Depends(contributor_service),
) -> Response:
    await svc.save(current_user.id, prompt_id)
    await missions.record_event(
        user=current_user,
        event_type="prompt_saved",
        prompt_id=prompt_id,
        source_event_key=f"prompt_saved:{current_user.id}:{prompt_id}",
    )
    await contributors.refresh_prompt_quality(prompt_id)
    await get_cache().bump_many(("prompts", "contributors", "recommendations"))
    return Response(status_code=204)


@router.delete("/me/saved-prompts/{prompt_id}", status_code=204)
async def unsave_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: SavedPromptService = Depends(saved_prompt_service),
    contributors: ContributorService = Depends(contributor_service),
) -> Response:
    await svc.unsave(current_user.id, prompt_id)
    await contributors.refresh_prompt_quality(prompt_id)
    await get_cache().bump_many(("prompts", "contributors", "recommendations"))
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    svc: UserService = Depends(user_service),
) -> UserRead:
    return await svc.get_by_id(user_id)
