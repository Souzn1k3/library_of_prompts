from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.core.cache import get_cache
from app.config import get_settings
from app.core.errors import AppError
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.analytics.repository.analytics_repository import AnalyticsRepository
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.education.model.lesson import LessonListItem, LessonRead, PopularLessonItem
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.education.service.lesson_service import LessonService
from app.modules.economy.repository.wallet_repository import WalletRepository
from app.modules.missions.repository.mission_repository import MissionRepository
from app.modules.missions.service.mission_service import MissionService
from app.modules.onboarding.repository.onboarding_repository import OnboardingRepository
from app.modules.catalog.repository.prompt_repository import PromptRepository

router = APIRouter(prefix="/lessons", tags=["lessons"])
_LESSON_CACHE_TTL = 120


def _lesson_visibility(viewer: User | None) -> str:
    if viewer is None:
        return "anon"
    return f"{viewer.role.value}:{viewer.plan_tier.value}"


def lesson_service(session: AsyncSession = Depends(get_db)) -> LessonService:
    return LessonService(LessonRepository(session))


def mission_service(session: AsyncSession = Depends(get_db)) -> MissionService:
    return MissionService(
        MissionRepository(session),
        OnboardingRepository(session),
        PromptRepository(session),
        wallet_repo=WalletRepository(session),
        analytics=AnalyticsService(AnalyticsRepository(session)),
    )


@router.get("", response_model=list[LessonListItem])
async def list_lessons(
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(lesson_service),
) -> list[LessonListItem]:
    cache = get_cache()
    visibility = _lesson_visibility(viewer)
    return await cache.get_or_set_json(
        namespace="lessons",
        suffix=f"list:visibility={visibility}",
        loader=lambda: svc.list_lessons(viewer),
        ttl_seconds=_LESSON_CACHE_TTL,
    )


@router.get("/popular", response_model=list[PopularLessonItem])
async def popular_lessons(
    limit: int = Query(default=8, ge=1, le=24),
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(lesson_service),
) -> list[PopularLessonItem]:
    cache = get_cache()
    visibility = _lesson_visibility(viewer)
    return await cache.get_or_set_json(
        namespace="lessons",
        suffix=f"popular:visibility={visibility}:limit={limit}",
        loader=lambda: svc.list_popular_lessons(viewer, limit=limit),
        ttl_seconds=_LESSON_CACHE_TTL,
    )


@router.get("/by-slug/{slug}", response_model=LessonRead)
async def get_lesson(
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(lesson_service),
    missions: MissionService = Depends(mission_service),
) -> LessonRead:
    lesson = await svc.get_by_slug(slug, viewer)
    if viewer is not None and not lesson.body_locked:
        await missions.record_event(
            user=viewer,
            event_type="lesson_viewed",
            lesson_id=lesson.id,
            source_event_key=f"lesson_viewed:{viewer.id}:{lesson.id}:{lesson.created_at.date().isoformat()}",
        )
    return lesson


@router.post("/by-slug/{slug}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_lesson(
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: LessonService = Depends(lesson_service),
    missions: MissionService = Depends(mission_service),
) -> Response:
    lesson = await svc.get_by_slug(slug, current_user)
    if lesson.body_locked:
        raise AppError(
            code="lesson_locked",
            message="Upgrade your plan to open this lesson.",
            status_code=403,
        )
    today_key = datetime.now(timezone.utc).date().isoformat()
    await missions.record_event(
        user=current_user,
        event_type="lesson_completed",
        lesson_id=lesson.id,
        source_event_key=f"lesson_completed:{current_user.id}:{lesson.id}",
    )
    await missions.record_event(
        user=current_user,
        event_type="streak_activity",
        lesson_id=lesson.id,
        source_event_key=f"streak_activity:{current_user.id}:{today_key}",
        payload={"source": "lesson_completed"},
    )
    await get_cache().bump_many(("lessons", "recommendations"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
