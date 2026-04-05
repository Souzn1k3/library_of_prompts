import uuid

from sqlalchemy import select

from app.infrastructure.db.models import StoreItem, StoreItemKind
from app.modules.economy.repository.store_repository_helpers import item_unlocks_prompt


class StoreRepositoryUnlockMixin:
    async def list_active_unlock_items(self) -> list[StoreItem]:
        stmt = (
            select(StoreItem)
            .where(
                StoreItem.is_active.is_(True),
                StoreItem.kind.in_([StoreItemKind.premium_prompt_unlock, StoreItemKind.prompt_bundle]),
            )
            .order_by(StoreItem.sort_order.asc(), StoreItem.created_at.asc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

    async def user_has_prompt_access(self, *, user_id: uuid.UUID, prompt_id: uuid.UUID) -> bool:
        purchases = await self.list_completed_unlock_purchases(user_id)
        return any(purchase.item is not None and item_unlocks_prompt(purchase.item, prompt_id) for purchase in purchases)

    async def list_owned_prompt_ids(self, *, user_id: uuid.UUID, prompt_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        ids = list(dict.fromkeys(prompt_ids))
        if not ids:
            return set()
        purchases = await self.list_completed_unlock_purchases(user_id)
        owned: set[uuid.UUID] = set()
        for purchase in purchases:
            item = purchase.item
            if item is None:
                continue
            for prompt_id in ids:
                if item_unlocks_prompt(item, prompt_id):
                    owned.add(prompt_id)
        return owned

    async def find_active_unlock_offer_for_prompt(self, prompt_id: uuid.UUID) -> StoreItem | None:
        items = await self.list_active_unlock_items()
        for item in items:
            if item_unlocks_prompt(item, prompt_id):
                return item
        return None
