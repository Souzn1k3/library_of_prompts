import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.infrastructure.db.models import Category, Prompt


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        parent_id: uuid.UUID | None = None,
        roots_only: bool = False,
    ) -> Sequence[Category]:
        q = select(Category).order_by(Category.sort_order, Category.name)
        if roots_only:
            q = q.where(Category.parent_id.is_(None))
        elif parent_id is not None:
            q = q.where(Category.parent_id == parent_id)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self._session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def count_children(self, category_id: uuid.UUID) -> int:
        q = select(func.count()).select_from(Category).where(Category.parent_id == category_id)
        result = await self._session.execute(q)
        return int(result.scalar_one() or 0)

    async def count_prompts(self, category_id: uuid.UUID) -> int:
        q = select(func.count()).select_from(Prompt).where(Prompt.category_id == category_id)
        result = await self._session.execute(q)
        return int(result.scalar_one() or 0)

    async def create(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def update(self, category: Category) -> Category:
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()

    async def get_by_id_or_raise(self, category_id: uuid.UUID) -> Category:
        row = await self.get_by_id(category_id)
        if row is None:
            raise NotFoundError("category", str(category_id))
        return row
