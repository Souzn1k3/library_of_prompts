from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_db
from app.modules.education.model.lesson import LessonListItem, LessonRead
from app.modules.education.repository.lesson_repository import LessonRepository
from app.modules.education.service.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["lessons"])


def lesson_service(session: AsyncSession = Depends(get_db)) -> LessonService:
    return LessonService(LessonRepository(session))


@router.get("", response_model=list[LessonListItem])
async def list_lessons(
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(lesson_service),
) -> list[LessonListItem]:
    return await svc.list_lessons(viewer)


@router.get("/by-slug/{slug}", response_model=LessonRead)
async def get_lesson(
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    svc: LessonService = Depends(lesson_service),
) -> LessonRead:
    return await svc.get_by_slug(slug, viewer)
