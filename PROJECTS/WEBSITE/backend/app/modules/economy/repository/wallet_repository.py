import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.infrastructure.db.models import (
    CurrencyTransaction,
    CurrencyTransactionType,
    MissionRewardType,
    User,
    UserCurrencyBalance,
)


class WalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _is_sqlite(self) -> bool:
        bind = self._session.bind
        return bool(bind and bind.dialect.name == "sqlite")

    def _insert(self, model):
        return sqlite_insert(model) if self._is_sqlite() else pg_insert(model)

    async def ensure_balance_row(self, user_id: uuid.UUID, *, for_update: bool = False) -> UserCurrencyBalance:
        stmt = select(UserCurrencyBalance).where(UserCurrencyBalance.user_id == user_id)
        if for_update and not self._is_sqlite():
            stmt = stmt.with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row:
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
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await self._session.execute(insert_stmt)
        row = (await self._session.execute(stmt)).scalar_one()
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
        metadata: dict | None = None,
        now: datetime | None = None,
    ) -> CurrencyTransaction:
        if amount == 0:
            raise AppError(
                code="invalid_amount",
                message="Amount must be non-zero.",
                status_code=400,
            )
        now = now or datetime.now(timezone.utc)
        balance_row = await self.ensure_balance_row(user_id, for_update=True)
        new_balance = balance_row.balance + amount
        if new_balance < 0:
            raise AppError(
                code="insufficient_funds",
                message="Not enough Lumens to complete this action.",
                status_code=400,
            )

        balance_row.balance = new_balance
        if amount > 0:
            balance_row.total_earned += amount
        else:
            balance_row.total_spent += abs(amount)

        await self._session.flush()
        await self._session.execute(
            update(User).where(User.id == user_id).values(mission_credits=new_balance)
        )

        txn = CurrencyTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            reason=reason,
            context=context,
            source_id=source_id,
            meta=metadata,
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
        return result.scalars().all()

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

    async def get_premium_unlock_until(self, user_id: uuid.UUID) -> datetime | None:
        row = await self._session.execute(select(User.premium_unlock_until).where(User.id == user_id))
        return row.scalar_one_or_none()

    async def record_daily_check_in(
        self,
        user_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> tuple[UserCurrencyBalance, bool]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)
        today = now.date()

        previous = row.last_check_in_at
        if previous is not None:
            previous_dt = previous if previous.tzinfo is not None else previous.replace(tzinfo=timezone.utc)
            previous_day = previous_dt.astimezone(timezone.utc).date()
            if previous_day == today:
                return row, False
            if previous_day == today - timedelta(days=1):
                row.current_streak = max(1, int(row.current_streak)) + 1
            else:
                row.current_streak = 1
        else:
            row.current_streak = 1

        row.best_streak = max(int(row.best_streak), int(row.current_streak))
        row.last_check_in_at = now
        await self._session.flush()
        await self._session.refresh(row)
        return row, True

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
