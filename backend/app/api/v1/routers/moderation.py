import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_moderator
from app.api.service_deps import build_analytics_service, build_contributor_service
from app.core.cache import get_cache
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.catalog.model.prompt import ModerationDecision, ModerationQueueItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributions.service.moderation_service import ModerationService

router = APIRouter(prefix="/moderation", tags=["moderation"])


def moderation_service(session: AsyncSession = Depends(get_db)) -> ModerationService:
    return ModerationService(
        PromptRepository(session),
        build_contributor_service(session),
        analytics=build_analytics_service(session),
    )


@router.get("/queue", response_model=list[ModerationQueueItem])
async def moderation_queue(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _mod: User = Depends(require_moderator),
    svc: ModerationService = Depends(moderation_service),
) -> list[ModerationQueueItem]:
    return await svc.queue(skip=skip, limit=limit)


@router.post("/{prompt_id}/decision", status_code=204)
async def moderation_decide(
    prompt_id: uuid.UUID,
    body: ModerationDecision,
    mod: User = Depends(require_moderator),
    svc: ModerationService = Depends(moderation_service),
) -> Response:
    await svc.decide(prompt_id, body, moderator=mod)
    await get_cache().bump_many(("prompts", "contributors"))
    return Response(status_code=204)
