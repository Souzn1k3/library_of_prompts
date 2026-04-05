import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.db.models import Prompt, PromptStatus, StoreItem


class StoreRepositoryItemMixin:
    async def rollback(self) -> None:
        await self._session.rollback()

    def add_item(self, item: StoreItem) -> None:
        self._session.add(item)

    async def try_add_item(self, item: StoreItem) -> bool:
        try:
            async with self._session.begin_nested():
                self._session.add(item)
                await self._session.flush()
        except IntegrityError:
            return False
        return True

    async def flush(self) -> None:
        await self._session.flush()

    async def list_active_items(self) -> list[StoreItem]:
        stmt = (
            select(StoreItem)
            .where(StoreItem.is_active.is_(True))
            .order_by(StoreItem.sort_order.asc(), StoreItem.created_at.asc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

    async def get_item_by_id(self, item_id: uuid.UUID) -> StoreItem | None:
        row = await self._session.execute(select(StoreItem).where(StoreItem.id == item_id))
        return row.scalar_one_or_none()

    async def get_item_by_slug(self, slug: str) -> StoreItem | None:
        row = await self._session.execute(select(StoreItem).where(StoreItem.slug == slug))
        return row.scalar_one_or_none()

    async def list_featured_premium_prompts(self, limit: int = 3) -> list[Prompt]:
        rows = await self._session.execute(
            select(Prompt)
            .where(
                Prompt.status == PromptStatus.published,
                Prompt.is_premium.is_(True),
            )
            .order_by(Prompt.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())
