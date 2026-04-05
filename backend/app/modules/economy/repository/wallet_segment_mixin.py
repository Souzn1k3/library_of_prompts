from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.infrastructure.db.models import (
    CurrencyTransaction,
    MissionCompletionEvent,
    PurchaseStatus,
    StoreItem,
    UserPurchase,
)
from app.modules.economy.config.tuning import (
    CATCHUP_BOOST_EXPIRY_HOURS,
    CATCHUP_BOOST_PCT,
    HOARDER_BALANCE_THRESHOLD,
    HOARDER_SPEND_RECENT_MAX,
    SEGMENT_MISSION_LOOKBACK_HOURS,
    SEGMENT_SPEND_LOOKBACK_DAYS,
    SPENDER_SPEND_RECENT_MIN,
)
from app.modules.economy.repository.wallet_constants import MISSION_EARNING_REASONS, SEGMENT_SPEND_REASONS


class WalletSegmentMixin:
    def _item_synergy_categories(self, item_meta: dict | None, purchase_meta: dict | None) -> set[str]:
        out: set[str] = set()
        for payload in (purchase_meta or {}, item_meta or {}):
            raw = payload.get("synergy_categories")
            if isinstance(raw, list):
                out.update(str(value).strip().lower() for value in raw if value)
            raw_single = payload.get("synergy_category")
            if isinstance(raw_single, str) and raw_single.strip():
                out.add(raw_single.strip().lower())
        return out

    async def owned_synergy_bonus(self, *, user_id: uuid.UUID, mission_category: str | None) -> int:
        category = (mission_category or "").strip().lower()
        if not category:
            return 0

        rows = await self._session.execute(
            select(UserPurchase.meta, StoreItem.meta)
            .join(StoreItem, StoreItem.id == UserPurchase.store_item_id)
            .where(
                UserPurchase.user_id == user_id,
                UserPurchase.status == PurchaseStatus.completed,
            )
            .order_by(UserPurchase.created_at.desc())
            .limit(120)
        )

        best_tier = 0
        for purchase_meta, item_meta in rows.all():
            categories = self._item_synergy_categories(item_meta, purchase_meta)
            if category not in categories:
                continue
            tier_raw = None
            for payload in (purchase_meta or {}, item_meta or {}):
                if payload.get("upgrade_tier") is not None:
                    tier_raw = payload.get("upgrade_tier")
                    break
            try:
                tier = int(tier_raw or 1)
            except (TypeError, ValueError):
                tier = 1
            best_tier = max(best_tier, tier)

        if best_tier <= 0:
            return 0
        return 2 if best_tier >= 2 else 1

    async def sum_mission_earnings_today(
        self,
        *,
        user_id: uuid.UUID,
        start_of_day: datetime,
        end_of_day: datetime,
    ) -> int:
        value = (
            await self._session.execute(
                select(func.coalesce(func.sum(CurrencyTransaction.amount), 0))
                .where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.reason.in_(MISSION_EARNING_REASONS),
                    CurrencyTransaction.created_at >= start_of_day,
                    CurrencyTransaction.created_at < end_of_day,
                )
            )
        ).scalar_one()
        return int(value or 0)

    async def count_mission_events_since(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        since: datetime,
        event_type: str | None = None,
    ) -> int:
        where = [
            MissionCompletionEvent.user_id == user_id,
            MissionCompletionEvent.mission_id == mission_id,
            MissionCompletionEvent.created_at >= since,
        ]
        if event_type is not None:
            where.append(MissionCompletionEvent.event_type == event_type)

        value = (
            await self._session.execute(
                select(func.count())
                .select_from(MissionCompletionEvent)
                .where(*where)
            )
        ).scalar_one()
        return int(value or 0)

    async def has_recent_mission_event(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        event_type: str,
        since: datetime,
    ) -> bool:
        row = (
            await self._session.execute(
                select(MissionCompletionEvent.id)
                .where(
                    MissionCompletionEvent.user_id == user_id,
                    MissionCompletionEvent.mission_id == mission_id,
                    MissionCompletionEvent.event_type == event_type,
                    MissionCompletionEvent.created_at >= since,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        return row is not None

    async def classify_user_segment(self, *, user_id: uuid.UUID, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id)
        balance = int(row.balance)

        mission_recent = (
            await self._session.execute(
                select(func.count())
                .select_from(MissionCompletionEvent)
                .where(
                    MissionCompletionEvent.user_id == user_id,
                    MissionCompletionEvent.created_at >= now - timedelta(hours=SEGMENT_MISSION_LOOKBACK_HOURS),
                )
            )
        ).scalar_one()
        mission_recent_count = int(mission_recent or 0)

        spend_recent = (
            await self._session.execute(
                select(func.count())
                .select_from(CurrencyTransaction)
                .where(
                    CurrencyTransaction.user_id == user_id,
                    CurrencyTransaction.amount < 0,
                    CurrencyTransaction.reason.in_(SEGMENT_SPEND_REASONS),
                    CurrencyTransaction.created_at >= now - timedelta(days=SEGMENT_SPEND_LOOKBACK_DAYS),
                )
            )
        ).scalar_one()
        spend_recent_count = int(spend_recent or 0)

        if mission_recent_count <= 0:
            return "inactive"
        if balance >= HOARDER_BALANCE_THRESHOLD and spend_recent_count <= HOARDER_SPEND_RECENT_MAX:
            return "hoarder"
        if spend_recent_count >= SPENDER_SPEND_RECENT_MIN:
            return "spender"
        return "balanced"

    async def resolve_catchup_boost(
        self,
        *,
        user_id: uuid.UUID,
        segment: str,
        now: datetime | None = None,
    ) -> tuple[float, int, bool]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        expires_at = row.catchup_boost_expires_at
        expires_dt = (
            expires_at
            if expires_at is not None and expires_at.tzinfo is not None
            else expires_at.replace(tzinfo=timezone.utc)
            if expires_at is not None
            else None
        )
        pct = max(0, int(row.catchup_boost_pct))

        if segment == "inactive":
            if expires_dt is None or expires_dt < now or pct <= 0:
                row.catchup_boost_pct = CATCHUP_BOOST_PCT
                row.catchup_boost_expires_at = now + timedelta(hours=CATCHUP_BOOST_EXPIRY_HOURS)
                await self._session.flush()
                return 1.0 + (CATCHUP_BOOST_PCT / 100.0), CATCHUP_BOOST_PCT, True

        if expires_dt is not None and expires_dt >= now and pct > 0:
            return 1.0 + (pct / 100.0), pct, False

        if expires_dt is not None and expires_dt < now and pct > 0:
            row.catchup_boost_pct = 0
            row.catchup_boost_expires_at = None
            await self._session.flush()

        return 1.0, 0, False
