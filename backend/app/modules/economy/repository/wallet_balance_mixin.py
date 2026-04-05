from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.errors import AppError
from app.infrastructure.db.models import (
    CurrencyTransaction,
    CurrencyTransactionType,
    MissionRewardType,
    User,
    UserCurrencyBalance,
)
from app.modules.economy.config.tuning import RANK_THRESHOLDS, SPEND_STREAK_MULTIPLIERS


class WalletBalanceMixin:
    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model: Any):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    def _rank_level(self, points: int) -> int:
        level = 1
        for index, threshold in enumerate(RANK_THRESHOLDS, start=1):
            if points >= threshold:
                level = index
            else:
                break
        return level

    def rank_next_threshold(self, level: int) -> int:
        index = max(1, level)
        if index >= len(RANK_THRESHOLDS):
            return RANK_THRESHOLDS[-1]
        return RANK_THRESHOLDS[index]

    def spend_streak_multiplier(self, streak_days: int) -> float:
        key = max(1, int(streak_days))
        if key >= 4:
            return SPEND_STREAK_MULTIPLIERS[4]
        return SPEND_STREAK_MULTIPLIERS[key]

    def _recompute_rank(self, row: UserCurrencyBalance) -> tuple[int, int]:
        points = int(row.total_earned + int(row.total_spent * 0.7))
        row.rank_points = points
        row.rank_level = self._rank_level(points)
        return row.rank_points, row.rank_level

    async def ensure_balance_row(self, user_id: uuid.UUID, *, for_update: bool = False) -> UserCurrencyBalance:
        stmt = select(UserCurrencyBalance).where(UserCurrencyBalance.user_id == user_id)
        if for_update and not self._is_sqlite():
            stmt = stmt.with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row:
            self._recompute_rank(row)
            return row

        user_row = await self._session.execute(select(User.mission_credits).where(User.id == user_id))
        starting_balance = int(user_row.scalar_one_or_none() or 0)
        insert_stmt = (
            self._insert(UserCurrencyBalance)
            .values(
                user_id=user_id,
                balance=starting_balance,
                total_earned=max(starting_balance, 0),
                total_spent=max(-starting_balance, 0),
                rank_points=max(starting_balance, 0),
                rank_level=1,
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await self._session.execute(insert_stmt)
        row = (await self._session.execute(stmt)).scalar_one()
        self._recompute_rank(row)
        return row

    async def get_balance_row(self, user_id: uuid.UUID, *, for_update: bool = False) -> UserCurrencyBalance:
        return await self.ensure_balance_row(user_id, for_update=for_update)

    async def adjust_balance(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        reason: CurrencyTransactionType,
        context: str | None = None,
        source_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> CurrencyTransaction:
        if amount == 0 and reason != CurrencyTransactionType.cashback_locked:
            raise AppError(
                code="invalid_amount",
                message="Amount must be non-zero.",
                status_code=400,
            )
        now = now or datetime.now(timezone.utc)
        balance_row = await self.ensure_balance_row(user_id, for_update=True)
        previous_rank_level = int(balance_row.rank_level)
        new_balance = int(balance_row.balance) + int(amount)
        if new_balance < 0:
            required_amount = abs(amount)
            missing_amount = max(0, required_amount - int(balance_row.balance))
            raise AppError(
                code="insufficient_funds",
                message="You need a few more Lumens to complete this action.",
                status_code=400,
                details={
                    "balance": int(balance_row.balance),
                    "required": required_amount,
                    "missing": missing_amount,
                },
                message_key="errors.insufficient_funds",
                message_params={
                    "missing": missing_amount,
                    "required": required_amount,
                },
            )

        if amount != 0:
            balance_row.balance = new_balance
            if amount > 0:
                balance_row.total_earned += amount
            else:
                balance_row.total_spent += abs(amount)

        rank_points, rank_level = self._recompute_rank(balance_row)
        rank_up = rank_level > previous_rank_level

        await self._session.flush()
        if amount != 0:
            await self._session.execute(
                update(User).where(User.id == user_id).values(mission_credits=new_balance)
            )

        merged_meta = dict(metadata or {})
        merged_meta.setdefault("rank_points", rank_points)
        merged_meta.setdefault("rank_level", rank_level)
        merged_meta.setdefault("rank_next_threshold", self.rank_next_threshold(rank_level))
        if rank_up:
            merged_meta["rank_up"] = True
            merged_meta["rank_level_from"] = previous_rank_level
            merged_meta["rank_level_to"] = rank_level

        txn = CurrencyTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            reason=reason,
            context=context,
            source_id=source_id,
            meta=merged_meta,
            created_at=now,
        )
        self._session.add(txn)
        await self._session.flush()
        await self._session.refresh(txn)
        return txn

    async def list_recent_transactions(self, user_id: uuid.UUID, limit: int = 20) -> list[CurrencyTransaction]:
        stmt = (
            select(CurrencyTransaction)
            .where(CurrencyTransaction.user_id == user_id)
            .order_by(CurrencyTransaction.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def has_transaction(self, *, user_id: uuid.UUID, reason: CurrencyTransactionType, context: str) -> bool:
        stmt = (
            select(CurrencyTransaction.id)
            .where(
                CurrencyTransaction.user_id == user_id,
                CurrencyTransaction.reason == reason,
                CurrencyTransaction.context == context,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def summary(self, user_id: uuid.UUID) -> tuple[int, int, int]:
        row = await self.ensure_balance_row(user_id)
        return int(row.balance), int(row.total_earned), int(row.total_spent)

    async def get_rank_snapshot(self, user_id: uuid.UUID) -> tuple[int, int, int]:
        row = await self.ensure_balance_row(user_id)
        return int(row.rank_points), int(row.rank_level), int(self.rank_next_threshold(int(row.rank_level)))

    async def get_premium_unlock_until(self, user_id: uuid.UUID) -> datetime | None:
        row = await self._session.execute(select(User.premium_unlock_until).where(User.id == user_id))
        return row.scalar_one_or_none()

    async def grant_reward_credits(
        self,
        *,
        user_id: uuid.UUID,
        mission_id: uuid.UUID,
        mission_slug: str,
        credits: int,
        now: datetime | None = None,
    ) -> None:
        if credits <= 0:
            return
        await self.adjust_balance(
            user_id=user_id,
            amount=credits,
            reason=CurrencyTransactionType.mission_reward,
            context=f"mission:{mission_slug}",
            source_id=mission_id,
            metadata={"type": MissionRewardType.credits.value, "mission_id": str(mission_id)},
            now=now,
        )
