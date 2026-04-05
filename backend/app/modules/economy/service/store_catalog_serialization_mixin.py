from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.errors import AppError
from app.infrastructure.db.models import StoreItem
from app.modules.economy.model.store import PurchaseRead, StoreItemRead


class StoreCatalogSerializationMixin:
    async def serialize_item(
        self,
        row: StoreItem,
        *,
        owned: bool = False,
        balance: int = 0,
        segment: str = "balanced",
        daily_offer_slugs: set[str] | None = None,
        offer_ends_at: datetime | None = None,
        active_boost_left_by_slug: dict[str, int] | None = None,
    ) -> StoreItemRead:
        sold_out = row.availability is not None and row.availability <= 0
        affordable = not sold_out and not owned and balance >= row.price
        remaining_lumens = max(row.price - balance, 0)
        progress_ratio = 1 if row.price <= 0 else round(min(balance, row.price) / row.price, 4)

        item_meta = row.meta or {}
        target_segment = str(item_meta.get("target_segment", "")).strip().lower()
        dynamic_offer = bool(target_segment and target_segment == segment)
        is_limited_offer = bool(daily_offer_slugs and row.slug in daily_offer_slugs)

        try:
            upgrade_tier = max(1, int(item_meta.get("upgrade_tier", 1)))
        except (TypeError, ValueError):
            upgrade_tier = 1
        try:
            max_tier = max(upgrade_tier, int(item_meta.get("max_tier", upgrade_tier)))
        except (TypeError, ValueError):
            max_tier = upgrade_tier

        boost_missions_left = None
        if active_boost_left_by_slug and row.slug in active_boost_left_by_slug:
            boost_missions_left = max(0, int(active_boost_left_by_slug[row.slug]))

        return StoreItemRead(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            price=row.price,
            kind=row.kind,
            availability=row.availability,
            metadata=row.meta,
            is_active=row.is_active,
            owned=owned,
            is_affordable=affordable,
            remaining_lumens=remaining_lumens,
            progress_ratio=progress_ratio,
            price_band=self._pricing.price_band(row.price),
            tags=self._pricing.item_tags(row),
            starter_type=item_meta.get("starter_type") if isinstance(item_meta.get("starter_type"), str) else None,
            is_limited_offer=is_limited_offer,
            offer_ends_at=offer_ends_at if is_limited_offer else None,
            offer_reason="daily_rotation" if is_limited_offer else ("personalized" if dynamic_offer else None),
            dynamic_offer=dynamic_offer,
            upgrade_tier=upgrade_tier,
            max_tier=max_tier,
            next_upgrade_cost=int(item_meta["next_upgrade_cost"]) if isinstance(item_meta.get("next_upgrade_cost"), int) else None,
            boost_pct=int(item_meta["boost_pct"]) if isinstance(item_meta.get("boost_pct"), int) else None,
            boost_missions_left=boost_missions_left,
            near_miss_delta=remaining_lumens,
        )

    async def serialize_purchase(
        self,
        purchase: Any,
        *,
        fallback_item: StoreItem | None = None,
        balance: int = 0,
    ) -> PurchaseRead:
        item = purchase.item or fallback_item
        if item is None:
            raise AppError(
                code="store_item_missing",
                message="Purchase item could not be loaded.",
                status_code=500,
                message_key="errors.store_item_missing",
            )
        return PurchaseRead(
            id=purchase.id,
            status=purchase.status,
            price_paid=purchase.price_paid,
            metadata=purchase.meta,
            client_token=purchase.client_token,
            item=await self.serialize_item(item, owned=True, balance=balance),
            created_at=purchase.created_at,
        )
