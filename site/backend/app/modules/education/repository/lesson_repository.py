from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Lesson


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
