from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Lesson, MissionCompletionEvent


class LessonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> Sequence[Lesson]:
        q = select(Lesson).order_by(Lesson.sort_order, Lesson.title)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_by_slug(self, slug: str) -> Lesson | None:
        result = await self._session.execute(select(Lesson).where(Lesson.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_id(self, lesson_id) -> Lesson | None:
        result = await self._session.execute(select(Lesson).where(Lesson.id == lesson_id))
        return result.scalar_one_or_none()

    async def list_popular(self, *, limit: int = 8) -> Sequence[tuple[Lesson, int]]:
        stmt = (
            select(
                Lesson,
                func.count(MissionCompletionEvent.id).label("completion_count"),
            )
            .outerjoin(MissionCompletionEvent, MissionCompletionEvent.lesson_id == Lesson.id)
            .group_by(Lesson.id)
            .order_by(
                func.count(MissionCompletionEvent.id).desc(),
                Lesson.sort_order.asc(),
                Lesson.title.asc(),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1] or 0)) for row in result.all()]
