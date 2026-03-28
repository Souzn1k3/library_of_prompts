import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import Prompt, PromptStatus, PurchaseStatus, StoreItem, StoreItemKind, UserPurchase


def _extract_prompt_ids(meta: dict | None) -> set[str]:
    if not meta:
        return set()
    raw_ids: list[str] = []
    prompt_id = meta.get("prompt_id")
    if prompt_id:
        raw_ids.append(str(prompt_id))
    prompt_ids = meta.get("prompt_ids")
    if isinstance(prompt_ids, list):
        raw_ids.extend(str(item) for item in prompt_ids if item)
    return {item for item in raw_ids if item}


def _item_unlocks_prompt(item: StoreItem, prompt_id: uuid.UUID) -> bool:
    prompt_id_str = str(prompt_id)
    prompt_ids = _extract_prompt_ids(item.meta)
    if item.kind == StoreItemKind.premium_prompt_unlock:
        return prompt_id_str in prompt_ids
    if item.kind == StoreItemKind.prompt_bundle:
        return prompt_id_str in prompt_ids
    return False


class StoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_items(self) -> list[StoreItem]:
        stmt = (
            select(StoreItem)
            .where(StoreItem.is_active.is_(True))
            .order_by(StoreItem.sort_order.asc(), StoreItem.created_at.asc())
        )
        rows = await self._session.execute(stmt)
        return rows.scalars().all()

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
        return rows.scalars().all()

    async def list_recent_purchases(self, user_id: uuid.UUID, *, limit: int = 20) -> list[UserPurchase]:
        stmt = (
            select(UserPurchase)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .options(selectinload(UserPurchase.item))
            .order_by(UserPurchase.created_at.desc())
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        return rows.scalars().all()

    async def list_all_completed_purchases(self, user_id: uuid.UUID) -> list[UserPurchase]:
        stmt = (
            select(UserPurchase)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .options(selectinload(UserPurchase.item))
            .order_by(UserPurchase.created_at.desc())
        )
        rows = await self._session.execute(stmt)
        return rows.scalars().all()

    async def get_purchase_by_client_token(self, *, user_id: uuid.UUID, client_token: str) -> UserPurchase | None:
        stmt = (
            select(UserPurchase)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.client_token == client_token,
            )
            .options(selectinload(UserPurchase.item))
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    async def get_completed_purchase_for_item(self, *, user_id: uuid.UUID, item_id: uuid.UUID) -> UserPurchase | None:
        stmt = (
            select(UserPurchase)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.store_item_id == item_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .options(selectinload(UserPurchase.item))
            .order_by(UserPurchase.created_at.desc())
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    async def user_has_prompt_access(self, *, user_id: uuid.UUID, prompt_id: uuid.UUID) -> bool:
        purchases = await self.list_all_completed_purchases(user_id)
        return any(purchase.item is not None and _item_unlocks_prompt(purchase.item, prompt_id) for purchase in purchases)

    async def find_active_unlock_offer_for_prompt(self, prompt_id: uuid.UUID) -> StoreItem | None:
        items = await self.list_active_items()
        for item in items:
            if _item_unlocks_prompt(item, prompt_id):
                return item
        return None

    async def create_purchase(
        self,
        *,
        user_id: uuid.UUID,
        item: StoreItem,
        price_paid: int,
        client_token: str | None,
        meta: dict | None,
    ) -> UserPurchase:
        purchase = UserPurchase(
            user_id=user_id,
            store_item_id=item.id,
            price_paid=price_paid,
            status=PurchaseStatus.completed,
            client_token=client_token,
            meta=meta,
        )
        self._session.add(purchase)
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase
