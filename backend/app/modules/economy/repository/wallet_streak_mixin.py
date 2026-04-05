from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.infrastructure.db.models import PurchaseStatus, UserCurrencyBalance, UserPurchase
from app.modules.economy.config.tuning import SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS


class WalletStreakMixin:
    async def apply_purchase_streak(self, user_id: uuid.UUID, *, now: datetime | None = None) -> tuple[int, float]:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        previous = row.last_spend_at
        today = now.date()
        if previous is None:
            row.spend_streak_days = 1
        else:
            previous_dt = previous if previous.tzinfo is not None else previous.replace(tzinfo=timezone.utc)
            previous_day = previous_dt.astimezone(timezone.utc).date()
            if previous_day == today:
                row.spend_streak_days = max(1, int(row.spend_streak_days))
            elif previous_day == today - timedelta(days=1):
                row.spend_streak_days = max(1, int(row.spend_streak_days)) + 1
            else:
                row.spend_streak_days = 1

        row.last_spend_at = now
        await self._session.flush()
        return int(row.spend_streak_days), self.spend_streak_multiplier(int(row.spend_streak_days))

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
            elif int(row.streak_freeze_tokens) > 0:
                # Preserve momentum once by consuming a freeze token.
                row.streak_freeze_tokens = max(0, int(row.streak_freeze_tokens) - 1)
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

    async def add_streak_freeze_tokens(self, user_id: uuid.UUID, amount: int = 1) -> int:
        if amount <= 0:
            return 0
        row = await self.ensure_balance_row(user_id, for_update=True)
        row.streak_freeze_tokens = int(row.streak_freeze_tokens) + amount
        await self._session.flush()
        return int(row.streak_freeze_tokens)

    async def should_offer_streak_recovery(
        self,
        *,
        user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> bool:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id)
        if int(row.current_streak) < 3:
            return False
        if row.last_check_in_at is None:
            return False
        previous_dt = (
            row.last_check_in_at
            if row.last_check_in_at.tzinfo is not None
            else row.last_check_in_at.replace(tzinfo=timezone.utc)
        )
        previous_day = previous_dt.astimezone(timezone.utc).date()
        today = now.date()
        return previous_day == (today - timedelta(days=1))

    async def track_second_purchase_challenge(self, *, user_id: uuid.UUID, now: datetime | None = None) -> str | None:
        now = now or datetime.now(timezone.utc)
        row = await self.ensure_balance_row(user_id, for_update=True)

        if row.second_purchase_challenge_started_at is None:
            row.second_purchase_challenge_started_at = now
            row.second_purchase_challenge_expires_at = now + timedelta(hours=SECOND_PURCHASE_CHALLENGE_WINDOW_HOURS)
            row.second_purchase_challenge_completed_at = None
            await self._session.flush()
            return "started"

        if row.second_purchase_challenge_completed_at is not None:
            return None

        expires_at = row.second_purchase_challenge_expires_at
        if expires_at is not None:
            expires_dt = expires_at if expires_at.tzinfo is not None else expires_at.replace(tzinfo=timezone.utc)
            if now > expires_dt:
                return "expired"

        started_at = row.second_purchase_challenge_started_at
        if started_at is None:
            return None

        started_dt = started_at if started_at.tzinfo is not None else started_at.replace(tzinfo=timezone.utc)
        purchase_count = (
            await self._session.execute(
                select(func.count())
                .select_from(UserPurchase)
                .where(
                    UserPurchase.user_id == user_id,
                    UserPurchase.status == PurchaseStatus.completed,
                    UserPurchase.created_at >= started_dt,
                )
            )
        ).scalar_one()

        if int(purchase_count or 0) >= 2:
            row.second_purchase_challenge_completed_at = now
            await self._session.flush()
            return "completed"
        return "in_progress"
