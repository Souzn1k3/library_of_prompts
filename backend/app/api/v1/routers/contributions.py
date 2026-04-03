from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_current_user
from app.api.service_deps import get_mission_service, get_submission_service
from app.core.cache import get_cache
from app.core.rate_limit import enforce_rate_limit, resolve_rate_limit_ip
from app.infrastructure.db.models import User
from app.modules.catalog.model.prompt import PromptSubmissionResult, PromptSubmit
from app.modules.contributions.service.submission_service import SubmissionService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/contributions", tags=["contributions"])


@router.post(
    "/submit",
    response_model=PromptSubmissionResult,
    status_code=status.HTTP_201_CREATED,
)
async def submit_prompt(
    request: Request,
    body: PromptSubmit,
    current_user: User = Depends(get_current_user),
    svc: SubmissionService = Depends(get_submission_service),
    missions: MissionService = Depends(get_mission_service),
) -> PromptSubmissionResult:
    ip = resolve_rate_limit_ip(request)
    await enforce_rate_limit(
        key=f"contributions:submit:user:{current_user.id}",
        limit=20,
        window_seconds=60 * 60,
    )
    await enforce_rate_limit(
        key=f"contributions:submit:ip:{ip}",
        limit=30,
        window_seconds=60 * 60,
    )
    result = await svc.submit(current_user, body)
    today_key = datetime.now(timezone.utc).date().isoformat()
    await missions.record_event(
        user=current_user,
        event_type="challenge_submitted",
        prompt_id=result.id,
        source_event_key=f"challenge_submitted:{current_user.id}:{result.id}",
        payload={"slug": result.slug},
    )
    await missions.record_event(
        user=current_user,
        event_type="streak_activity",
        prompt_id=result.id,
        source_event_key=f"streak_activity:{current_user.id}:{today_key}",
        payload={"source": "challenge_submitted", "slug": result.slug},
    )
    await get_cache().bump_many(("prompts", "contributors", "lessons"))
    return result
