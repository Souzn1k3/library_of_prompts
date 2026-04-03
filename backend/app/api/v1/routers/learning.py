from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user, get_optional_user
from app.api.service_deps import get_learning_service, get_mission_service, get_store_service
from app.core.i18n import resolve_language_from_header
from app.infrastructure.db.models import User
from app.modules.learning.model.learning import (
    LearningCatalogRead,
    LearningCourseRead,
    LearningLessonRead,
    LearningMyModulesRead,
    LearningStartTargetRead,
    LearningStepSubmitRead,
    LearningStepSubmitRequest,
)
from app.modules.learning.service.learning_service import LearningService
from app.modules.missions.service.mission_service import MissionService
from app.modules.economy.service.store_service import StoreService

router = APIRouter(prefix="/learning", tags=["learning"])


def _language(request: Request):
    return resolve_language_from_header(request.headers.get("accept-language"))


@router.get("/start-target", response_model=LearningStartTargetRead)
async def learning_start_target(
    request: Request,
    viewer: User | None = Depends(get_optional_user),
    svc: LearningService = Depends(get_learning_service),
) -> LearningStartTargetRead:
    return await svc.start_target(viewer)


@router.get("/courses", response_model=LearningCatalogRead)
async def learning_catalog(
    request: Request,
    viewer: User | None = Depends(get_optional_user),
    svc: LearningService = Depends(get_learning_service),
) -> LearningCatalogRead:
    return await svc.catalog(user=viewer, language=_language(request))


@router.get("/my", response_model=LearningMyModulesRead)
async def my_learning_modules(
    request: Request,
    current_user: User = Depends(get_current_user),
    svc: LearningService = Depends(get_learning_service),
) -> LearningMyModulesRead:
    return await svc.my_modules(user=current_user, language=_language(request))


@router.get("/courses/{course_slug}", response_model=LearningCourseRead)
async def get_learning_course(
    request: Request,
    course_slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: LearningService = Depends(get_learning_service),
) -> LearningCourseRead:
    return await svc.course(course_slug=course_slug, user=viewer, language=_language(request))


@router.get("/courses/{course_slug}/lessons/{lesson_slug}", response_model=LearningLessonRead)
async def get_learning_lesson(
    request: Request,
    course_slug: str,
    lesson_slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: LearningService = Depends(get_learning_service),
) -> LearningLessonRead:
    return await svc.lesson(
        user=viewer,
        course_slug=course_slug,
        lesson_slug=lesson_slug,
        language=_language(request),
    )


@router.post(
    "/courses/{course_slug}/lessons/{lesson_slug}/steps/{step_slug}/submit",
    response_model=LearningStepSubmitRead,
)
async def submit_learning_step(
    request: Request,
    course_slug: str,
    lesson_slug: str,
    step_slug: str,
    body: LearningStepSubmitRequest,
    current_user: User = Depends(get_current_user),
    svc: LearningService = Depends(get_learning_service),
    missions: MissionService = Depends(get_mission_service),
    store: StoreService = Depends(get_store_service),
) -> LearningStepSubmitRead:
    return await svc.submit_step(
        user=current_user,
        course_slug=course_slug,
        lesson_slug=lesson_slug,
        step_slug=step_slug,
        answer=body.answer,
        language=_language(request),
        missions=missions,
        store=store,
    )


@router.get("/lessons/by-slug/{lesson_slug}/locate")
async def locate_learning_lesson(
    lesson_slug: str,
    svc: LearningService = Depends(get_learning_service),
) -> dict[str, str] | None:
    row = await svc.locate_lesson(lesson_slug)
    if row is None:
        return None
    course_slug, normalized_lesson_slug = row
    return {
        "course_slug": course_slug,
        "lesson_slug": normalized_lesson_slug,
        "href": f"/learn/course/{course_slug}/lesson/{normalized_lesson_slug}",
    }

