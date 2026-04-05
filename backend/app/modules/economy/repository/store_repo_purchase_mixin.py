import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import PurchaseStatus, StoreItem, StoreItemKind, UserPurchase


class StoreRepositoryPurchaseMixin:
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
        return list(rows.scalars().all())

    async def has_completed_purchase(self, user_id: uuid.UUID) -> bool:
        stmt = (
            select(UserPurchase.id)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .limit(1)
        )
        rows = await self._session.execute(stmt)
        return rows.scalar_one_or_none() is not None

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
        return list(rows.scalars().all())

    async def list_owned_one_time_item_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        stmt = (
            select(UserPurchase.store_item_id)
            .join(StoreItem, StoreItem.id == UserPurchase.store_item_id)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
                StoreItem.kind.in_(
                    [
                        StoreItemKind.starter,
                        StoreItemKind.subscription_discount,
                        StoreItemKind.premium_prompt_unlock,
                        StoreItemKind.prompt_bundle,
                        StoreItemKind.boost,
                    ]
                ),
            )
        )
        rows = await self._session.execute(stmt)
        return {row[0] for row in rows.all()}

    async def list_completed_unlock_purchases(self, user_id: uuid.UUID) -> list[UserPurchase]:
        stmt = (
            select(UserPurchase)
            .join(StoreItem, StoreItem.id == UserPurchase.store_item_id)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
                StoreItem.kind.in_([StoreItemKind.premium_prompt_unlock, StoreItemKind.prompt_bundle]),
            )
            .options(selectinload(UserPurchase.item))
            .order_by(UserPurchase.created_at.desc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

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

    async def decrement_availability_if_available(self, item_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            update(StoreItem)
            .where(
                StoreItem.id == item_id,
                StoreItem.availability.is_not(None),
                StoreItem.availability > 0,
            )
            .values(availability=StoreItem.availability - 1)
        )
        return int(getattr(result, "rowcount", 0) or 0) > 0

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

    async def try_create_purchase(
        self,
        *,
        user_id: uuid.UUID,
        item: StoreItem,
        price_paid: int,
        client_token: str | None,
        meta: dict | None,
    ) -> UserPurchase | None:
        purchase = UserPurchase(
            user_id=user_id,
            store_item_id=item.id,
            price_paid=price_paid,
            status=PurchaseStatus.completed,
            client_token=client_token,
            meta=meta,
        )
        try:
            async with self._session.begin_nested():
                self._session.add(purchase)
                await self._session.flush()
        except Exception as exc:
            message = str(exc).lower()
            if "ix_user_purchases_client_token" in message or (
                "duplicate key value violates unique constraint" in message and "client_token" in message
            ):
                return None
            raise
        await self._session.refresh(purchase)
        return purchase
