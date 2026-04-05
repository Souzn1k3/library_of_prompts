from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.db.models import User
from app.modules.economy.model.store import StoreItemRead


class StoreCatalogListingMixin:
    def _active_boost_left_by_slug(self, boost_rows: list[object]) -> dict[str, int]:
        remaining_by_slug: dict[str, int] = {}
        for row in boost_rows:
            if not isinstance(getattr(row, "meta", None), dict) or not isinstance(row.meta.get("item_slug"), str):
                continue
            slug = str(row.meta["item_slug"])
            remaining_by_slug[slug] = max(
                remaining_by_slug.get(slug, 0),
                max(0, int(row.missions_total) - int(row.missions_used)),
            )
        return remaining_by_slug

    async def list_items(self, user: User, *, balance: int | None = None) -> list[StoreItemRead]:
        items = await self._store.list_active_items()
        if not items:
            premium_prompts = await self._store.list_featured_premium_prompts(limit=3)
            items = self.build_default_items(premium_prompts, stable_ids=True)

        if balance is None:
            balance, _, _ = await self._wallet_repo.summary(user.id)

        owned_item_ids = await self._store.list_owned_one_time_item_ids(user.id)
        segment = await self._wallet_repo.classify_user_segment(user_id=user.id)
        now = datetime.now(timezone.utc)
        payer_status = await self.payer_status(user.id)
        daily_offer_slugs = self.daily_offer_rotation(items, now=now)
        offer_ends_at = self.offer_window(now)

        active_boost_rows = await self._wallet_repo.list_active_boosts(user_id=user.id, now=now)
        active_boost_left_by_slug = self._active_boost_left_by_slug(active_boost_rows)

        serialized = [
            await self.serialize_item(
                item,
                owned=item.id in owned_item_ids,
                balance=balance,
                segment=segment,
                daily_offer_slugs=daily_offer_slugs,
                offer_ends_at=offer_ends_at,
                active_boost_left_by_slug=active_boost_left_by_slug,
            )
            for item in items
        ]
        await self.track_store_experiment_view(
            user=user,
            payer_status=payer_status,
            now=now,
            offer_slugs=daily_offer_slugs,
        )
        return sorted(
            serialized,
            key=lambda item: (
                not item.is_limited_offer,
                item.price,
                item.remaining_lumens,
                item.title.lower(),
            ),
        )
