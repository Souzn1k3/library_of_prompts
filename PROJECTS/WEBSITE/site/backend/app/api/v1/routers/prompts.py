import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.infrastructure.db.models import PromptTechnique, User
from app.infrastructure.db.session import get_db
from app.modules.catalog.model.prompt import PromptListItem, PromptRead
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.catalog.service.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


def prompt_service(session: AsyncSession = Depends(get_db)) -> PromptService:
    return PromptService(PromptRepository(session))


@router.get("", response_model=list[PromptListItem])
async def list_prompts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    q: str | None = Query(default=None, description="Search title, summary, body"),
    category_id: uuid.UUID | None = Query(default=None),
    technique: PromptTechnique | None = Query(default=None),
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(prompt_service),
) -> list[PromptListItem]:
    return await svc.list_published(
        viewer,
        skip=skip,
        limit=limit,
        q=q,
        category_id=category_id,
        technique=technique,
    )


@router.get("/by-slug/{slug}", response_model=PromptRead)
async def get_prompt_by_slug(
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(prompt_service),
) -> PromptRead:
    return await svc.get_by_slug(slug, viewer)


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(
    prompt_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PromptService = Depends(prompt_service),
) -> PromptRead:
    return await svc.get_by_id(prompt_id, viewer)
