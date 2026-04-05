from __future__ import annotations

from typing import Any

from app.infrastructure.db.models import StoreItem, User
from app.modules.economy.config.tuning import NEAR_MISS_MAX_DELTA
from app.modules.economy.model.store import EconomyActionRead
from app.modules.economy.service.store_default_catalog import build_default_store_items


class StoreCatalogFeedbackMixin:
    async def build_action_feedback(
        self,
        user: User,
        *,
        previous_balance: int | None = None,
        completed_mission_slugs: list[str] | None = None,
    ) -> EconomyActionRead:
        wallet = await self._wallet.get_wallet(user, limit=20)
        items = await self.list_items(user, balance=wallet.balance)
        available_items = [item for item in items if item.is_affordable]
        newly_affordable_items = (
            [item for item in available_items if previous_balance is not None and previous_balance < item.price]
            if previous_balance is not None
            else []
        )
        next_target = next(
            (item for item in items if not item.owned and not item.is_affordable and item.remaining_lumens > 0),
            None,
        )
        near_miss_message = (
            f"You need {next_target.remaining_lumens} LMN more for {next_target.title}."
            if next_target is not None and next_target.remaining_lumens <= NEAR_MISS_MAX_DELTA
            else None
        )
        return EconomyActionRead(
            wallet=wallet,
            balance=wallet.balance,
            available_items=available_items,
            newly_affordable_items=newly_affordable_items,
            best_item=self._pricing.pick_best_item(items),
            balance_delta=(wallet.balance - previous_balance) if previous_balance is not None else 0,
            completed_mission_slugs=completed_mission_slugs or [],
            near_miss_message=near_miss_message,
        )

    def build_default_items(self, premium_prompts: list[Any], *, stable_ids: bool = False) -> list[StoreItem]:
        return build_default_store_items(premium_prompts, stable_ids=stable_ids)

    async def sync_default_items(self) -> list[StoreItem]:
        premium_prompts = await self._store.list_featured_premium_prompts(limit=3)
        defaults = self.build_default_items(premium_prompts)

        for item in defaults:
            existing = await self._store.get_item_by_slug(item.slug)
            if existing is None:
                inserted = await self._store.try_add_item(item)
                if inserted:
                    continue
                existing = await self._store.get_item_by_slug(item.slug)
                if existing is None:
                    continue
            existing.title = item.title
            existing.description = item.description
            existing.price = item.price
            existing.kind = item.kind
            existing.meta = item.meta
            existing.sort_order = item.sort_order
            existing.is_active = True

        await self._store.flush()
        return await self._store.list_active_items()
