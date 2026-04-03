import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.catalog.model.prompt import AuthorPromptRow, PromptListItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.identity.model.user import UserRead
from app.modules.identity.model.user_update import UserUpdateMe
from app.modules.identity.repository.saved_prompt_repository import SavedPromptRepository
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.identity.service.saved_prompt_service import SavedPromptService
from app.modules.identity.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(session))


def saved_prompt_service(session: AsyncSession = Depends(get_db)) -> SavedPromptService:
    return SavedPromptService(
        SavedPromptRepository(session),
        PromptRepository(session),
    )


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
) -> list[AuthorPromptRow]:
    repo = PromptRepository(session)
    rows = await repo.list_by_author(current_user.id, skip=0, limit=100)
    return [AuthorPromptRow.model_validate(r) for r in rows]


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
) -> Response:
    await svc.save(current_user.id, prompt_id)
    return Response(status_code=204)


@router.delete("/me/saved-prompts/{prompt_id}", status_code=204)
async def unsave_prompt(
    prompt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    svc: SavedPromptService = Depends(saved_prompt_service),
) -> Response:
    await svc.unsave(current_user.id, prompt_id)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    svc: UserService = Depends(user_service),
) -> UserRead:
    return await svc.get_by_id(user_id)
