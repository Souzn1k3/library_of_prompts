import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_moderator
from app.core.cache import get_cache
from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.model.prompt import ModerationDecision, ModerationQueueItem
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.contributions.service.moderation_service import ModerationService
from app.modules.identity.repository.user_repository import UserRepository

router = APIRouter(prefix="/moderation", tags=["moderation"])


def moderation_service(session: AsyncSession = Depends(get_db)) -> ModerationService:
    return ModerationService(
        PromptRepository(session),
        ContributorService(ContributorRepository(session), UserRepository(session)),
        analytics=AnalyticsService(AnalyticsRepository(session)),
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
