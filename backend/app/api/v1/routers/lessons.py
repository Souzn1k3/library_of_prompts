from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_current_user, get_optional_user
from app.api.service_deps import get_lesson_service, get_mission_service, get_store_service
from app.core.cache import get_cache
from app.core.errors import AppError
from app.core.i18n import SupportedLanguage, resolve_language_from_header
from app.infrastructure.db.models import User
from app.modules.economy.model.store import EconomyActionRead
from app.modules.economy.service.store_service import StoreService
from app.modules.education.model.lesson import LessonListItem, LessonRead, PopularLessonItem
from app.modules.education.service.lesson_service import LessonService
from app.modules.missions.service.mission_service import MissionService

router = APIRouter(prefix="/lessons", tags=["lessons"])
_LESSON_CACHE_TTL = 120


def _lesson_visibility(viewer: User | None) -> str:
    if viewer is None:
        return "anon"
    return f"{viewer.role.value}:{viewer.plan_tier.value}"


def _language(request: Request) -> SupportedLanguage:
    return resolve_language_from_header(request.headers.get("accept-language"))


@router.get("", response_model=list[LessonListItem])
async def list_lessons(
    request: Request,
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(get_lesson_service),
) -> list[LessonListItem]:
    cache = get_cache()
    visibility = _lesson_visibility(viewer)
    language = _language(request)
    return await cache.get_or_set_json(
        namespace="lessons",
        suffix=f"list:visibility={visibility}:language={language}",
        loader=lambda: svc.list_lessons(viewer, language=language),
        ttl_seconds=_LESSON_CACHE_TTL,
    )


@router.get("/popular", response_model=list[PopularLessonItem])
async def popular_lessons(
    request: Request,
    limit: int = Query(default=8, ge=1, le=24),
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(get_lesson_service),
) -> list[PopularLessonItem]:
    cache = get_cache()
    visibility = _lesson_visibility(viewer)
    language = _language(request)
    return await cache.get_or_set_json(
        namespace="lessons",
        suffix=f"popular:visibility={visibility}:limit={limit}:language={language}",
        loader=lambda: svc.list_popular_lessons(viewer, limit=limit, language=language),
        ttl_seconds=_LESSON_CACHE_TTL,
    )


@router.get("/by-slug/{slug}", response_model=LessonRead)
async def get_lesson(
    request: Request,
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(get_lesson_service),
    missions: MissionService = Depends(get_mission_service),
) -> LessonRead:
    lesson = await svc.get_by_slug(slug, viewer, language=_language(request))
    if viewer is not None and not lesson.body_locked:
        await missions.record_event(
            user=viewer,
            event_type="lesson_viewed",
            lesson_id=lesson.id,
            source_event_key=f"lesson_viewed:{viewer.id}:{lesson.id}:{lesson.created_at.date().isoformat()}",
        )
    return lesson


@router.post("/by-slug/{slug}/complete", response_model=EconomyActionRead)
async def complete_lesson(
    request: Request,
    slug: str,
    current_user: User = Depends(get_current_user),
    svc: LessonService = Depends(get_lesson_service),
    missions: MissionService = Depends(get_mission_service),
    store: StoreService = Depends(get_store_service),
) -> EconomyActionRead:
    lesson = await svc.get_by_slug(slug, current_user, language=_language(request))
    if lesson.body_locked:
        raise AppError(
            code="lesson_locked",
            message="Upgrade your plan to open this lesson.",
            status_code=403,
        )
    previous_balance = (await store.wallet(current_user)).balance
    today_key = datetime.now(timezone.utc).date().isoformat()
    completed = await missions.record_event(
        user=current_user,
        event_type="lesson_completed",
        lesson_id=lesson.id,
        source_event_key=f"lesson_completed:{current_user.id}:{lesson.id}",
    )
    completed.extend(
        await missions.record_event(
            user=current_user,
            event_type="streak_activity",
            lesson_id=lesson.id,
            source_event_key=f"streak_activity:{current_user.id}:{today_key}",
            payload={"source": "lesson_completed"},
        )
    )
    await get_cache().bump_many(("lessons", "recommendations"))
    return await store.build_action_feedback(
        current_user,
        previous_balance=previous_balance,
        completed_mission_slugs=list(dict.fromkeys(completed)),
    )
