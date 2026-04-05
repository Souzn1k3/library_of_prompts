from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update

from app.infrastructure.db.models import (
    BoostStatus,
    CurrencyTransactionType,
    LockedRewardStatus,
    UserActiveBoost,
    UserLockedReward,
)
from app.modules.economy.config.tuning import LOCKED_CASHBACK_REQUIRED_MISSIONS


class WalletRewardMixin:
    async def list_pending_locked_rewards(self, user_id: uuid.UUID) -> list[UserLockedReward]:
        now = datetime.now(timezone.utc)
        await self.expire_locked_rewards(user_id=user_id, now=now)
        stmt = (
            select(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
            )
            .order_by(UserLockedReward.created_at.asc())
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

    async def create_locked_cashback(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        source_purchase_id: uuid.UUID | None,
        unlock_by: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> UserLockedReward | None:
        if amount <= 0:
            return None
        reward = UserLockedReward(
            user_id=user_id,
            source_purchase_id=source_purchase_id,
            amount=amount,
            required_mission_count=LOCKED_CASHBACK_REQUIRED_MISSIONS,
            completed_mission_count=0,
            status=LockedRewardStatus.pending,
            unlock_by=unlock_by,
            meta=metadata,
        )
        self._session.add(reward)
        await self._session.flush()
        await self._session.refresh(reward)
        return reward

    async def expire_locked_rewards(self, *, user_id: uuid.UUID, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        stmt = (
            update(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
                UserLockedReward.unlock_by.is_not(None),
                UserLockedReward.unlock_by < now,
            )
            .values(status=LockedRewardStatus.expired, expired_at=now)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return int(getattr(result, "rowcount", 0) or 0)

    async def progress_locked_cashback(
        self,
        *,
        user_id: uuid.UUID,
        mission_progress: int = 1,
        now: datetime | None = None,
    ) -> list[UserLockedReward]:
        now = now or datetime.now(timezone.utc)
        if mission_progress <= 0:
            return []

        await self.expire_locked_rewards(user_id=user_id, now=now)

        stmt = (
            select(UserLockedReward)
            .where(
                UserLockedReward.user_id == user_id,
                UserLockedReward.status == LockedRewardStatus.pending,
                (UserLockedReward.unlock_by.is_(None) | (UserLockedReward.unlock_by >= now)),
            )
            .order_by(UserLockedReward.created_at.asc())
        )
        if not self._is_sqlite():
            stmt = stmt.with_for_update()

        rows = (await self._session.execute(stmt)).scalars().all()

        unlocked: list[UserLockedReward] = []
        for row in rows:
            row.completed_mission_count = int(row.completed_mission_count) + mission_progress
            if int(row.completed_mission_count) >= int(row.required_mission_count):
                row.status = LockedRewardStatus.unlocked
                row.unlocked_at = now
                unlocked.append(row)

        await self._session.flush()

        for row in unlocked:
            await self.adjust_balance(
                user_id=user_id,
                amount=int(row.amount),
                reason=CurrencyTransactionType.cashback_unlocked,
                context=f"cashback_unlock:{row.id}",
                source_id=row.id,
                metadata={
                    "locked_reward_id": str(row.id),
                    "source_purchase_id": str(row.source_purchase_id) if row.source_purchase_id else None,
                    "required_mission_count": int(row.required_mission_count),
                },
                now=now,
            )

        return unlocked

    async def grant_active_boost(
        self,
        *,
        user_id: uuid.UUID,
        source_purchase_id: uuid.UUID | None,
        boost_percent: int,
        missions_total: int,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UserActiveBoost | None:
        if boost_percent <= 0 or missions_total <= 0:
            return None
        boost = UserActiveBoost(
            user_id=user_id,
            source_purchase_id=source_purchase_id,
            boost_percent=boost_percent,
            missions_total=missions_total,
            missions_used=0,
            status=BoostStatus.active,
            expires_at=expires_at,
            meta=metadata,
        )
        self._session.add(boost)
        await self._session.flush()
        await self._session.refresh(boost)
        return boost

    async def _expire_old_boosts(self, user_id: uuid.UUID, *, now: datetime) -> None:
        await self._session.execute(
            update(UserActiveBoost)
            .where(
                UserActiveBoost.user_id == user_id,
                UserActiveBoost.status == BoostStatus.active,
                UserActiveBoost.expires_at.is_not(None),
                UserActiveBoost.expires_at < now,
            )
            .values(status=BoostStatus.expired)
        )

    async def list_active_boosts(self, *, user_id: uuid.UUID, now: datetime | None = None) -> list[UserActiveBoost]:
        now = now or datetime.now(timezone.utc)
        await self._expire_old_boosts(user_id, now=now)
        rows = await self._session.execute(
            select(UserActiveBoost)
            .where(
                UserActiveBoost.user_id == user_id,
                UserActiveBoost.status == BoostStatus.active,
            )
            .order_by(UserActiveBoost.created_at.asc())
        )
        return list(rows.scalars().all())

    async def consume_active_boost(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> tuple[float, int | None, int | None]:
        now = now or datetime.now(timezone.utc)
        await self._expire_old_boosts(user_id, now=now)

        row = (
            await self._session.execute(
                select(UserActiveBoost)
                .where(
                    UserActiveBoost.user_id == user_id,
                    UserActiveBoost.status == BoostStatus.active,
                )
                .order_by(UserActiveBoost.created_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if row is None:
            return 1.0, None, None

        row.missions_used = int(row.missions_used) + 1
        if int(row.missions_used) >= int(row.missions_total):
            row.status = BoostStatus.exhausted
        await self._session.flush()

        missions_left = max(0, int(row.missions_total) - int(row.missions_used))
        return 1.0 + (int(row.boost_percent) / 100.0), int(row.boost_percent), missions_left
