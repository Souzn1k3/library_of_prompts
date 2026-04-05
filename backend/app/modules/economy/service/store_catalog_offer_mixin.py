from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.infrastructure.db.models import StoreItem, StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.economy.config.tuning import DAILY_OFFER_ROTATION_SIZE
from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_NAME,
    economy_experiment_metadata,
)


class StoreCatalogOfferMixin:
    def is_one_time_item(self, item: StoreItem) -> bool:
        return item.kind in {
            StoreItemKind.starter,
            StoreItemKind.subscription_discount,
            StoreItemKind.premium_prompt_unlock,
            StoreItemKind.prompt_bundle,
            StoreItemKind.boost,
        }

    def offer_window(self, now: datetime) -> datetime:
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return start + timedelta(days=1)

    def daily_offer_rotation(self, items: list[StoreItem], *, now: datetime) -> set[str]:
        active = [item for item in items if item.is_active and (item.availability is None or item.availability > 0)]
        if not active:
            return set()
        seed = now.date().isoformat()
        scored = sorted(active, key=lambda item: sha256(f"{seed}:{item.slug}".encode("utf-8")).hexdigest())
        return {item.slug for item in scored[:DAILY_OFFER_ROTATION_SIZE]}

    async def payer_status(self, user_id: uuid.UUID) -> str:
        return "payer" if await self._store.has_completed_purchase(user_id) else "non_payer"

    async def track_store_experiment_view(
        self,
        *,
        user: User,
        payer_status: str,
        now: datetime,
        offer_slugs: set[str],
    ) -> None:
        if self._analytics is None:
            return

        experiment_meta = economy_experiment_metadata(user_id=user.id, payer_status=payer_status)
        variant = experiment_meta["experiment_variant"]
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.economy_experiment_assigned,
            user_id=user.id,
            metadata=experiment_meta,
            context_page="/api/v1/store",
            context_feature="ab_assignment",
            event_id=f"{ECONOMY_EXPERIMENT_NAME}:{user.id}:{payer_status}",
        )
        await self._analytics.record_server_event(
            event_name=AnalyticsEventName.store_offer_viewed,
            user_id=user.id,
            metadata={
                **experiment_meta,
                "offer_count": len(offer_slugs),
                "offer_slugs": sorted(offer_slugs),
                "offer_day": now.date().isoformat(),
            },
            context_page="/api/v1/store",
            context_feature="offer_impression",
            event_id=f"store_offer_viewed:{user.id}:{variant}:{now.date().isoformat()}",
        )
