from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.cache import get_cache
from app.config import get_settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.catalog.model.prompt import PromptSubmissionResult, PromptSubmit
from app.modules.catalog.repository.category_repository import CategoryRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository
from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_service import ContributorService
from app.modules.contributions.service.submission_service import SubmissionService
from app.modules.identity.repository.user_repository import UserRepository

router = APIRouter(prefix="/contributions", tags=["contributions"])


def submission_service(session: AsyncSession = Depends(get_db)) -> SubmissionService:
    return SubmissionService(
        PromptRepository(session),
        CategoryRepository(session),
        ContributorService(ContributorRepository(session), UserRepository(session)),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


@router.post(
    "/submit",
    response_model=PromptSubmissionResult,
    status_code=status.HTTP_201_CREATED,
)
async def submit_prompt(
    body: PromptSubmit,
    current_user: User = Depends(get_current_user),
    svc: SubmissionService = Depends(submission_service),
) -> PromptSubmissionResult:
    result = await svc.submit(current_user, body)
    await get_cache().bump_many(("prompts", "contributors", "lessons"))
    return result
