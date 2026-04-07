from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.infrastructure.db.models import CurrencyTransactionType, User
from app.modules.economy.config.tuning import (
    DAILY_LADDER_REWARDS,
    STREAK_FREEZE_TOKEN_MILESTONES,
    STREAK_MILESTONE_REWARDS,
)


class WalletActionsMixin:
    async def ensure_wallet(self, user_id: uuid.UUID) -> None:
        await self._repo.ensure_balance_row(user_id)

    async def adjust(
        self,
        *,
        user_id: uuid.UUID,
        amount: int,
        reason: CurrencyTransactionType,
        context: str | None = None,
        source_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        now: datetime | None = None,
    ) -> None:
        await self._repo.adjust_balance(
            user_id=user_id,
            amount=amount,
            reason=reason,
            context=context,
            source_id=source_id,
            metadata=metadata,
            now=now,
        )

    async def reward_mission(self, *, user_id: uuid.UUID, mission_id: uuid.UUID, mission_slug: str, credits: int) -> None:
        await self._repo.grant_reward_credits(
            user_id=user_id,
            mission_id=mission_id,
            mission_slug=mission_slug,
            credits=credits,
        )

    async def grant_premium_days(self, user: User, days: int) -> datetime:
        now = datetime.now(timezone.utc)
        desired = now + timedelta(days=days)
        current = user.premium_unlock_until
        if current is not None and current > desired:
            desired = current
        user.premium_unlock_until = desired
        return desired

    async def apply_streak_bonus(self, user_id: uuid.UUID, amount: int, *, today: datetime | None = None) -> None:
        today = today or datetime.now(timezone.utc)
        await self.adjust(
            user_id=user_id,
            amount=amount,
            reason=CurrencyTransactionType.streak_bonus,
            context=f"streak:{today.date().isoformat()}",
            metadata={"streak_bonus": True},
            now=today,
        )

    async def daily_checkin_bonus(self, user_id: uuid.UUID, *, amount: int = 2) -> None:
        now = datetime.now(timezone.utc)
        balance_row, applied = await self._repo.record_daily_check_in(user_id, now=now)
        if not applied:
            return

        streak_day = max(1, int(balance_row.current_streak))
        ladder_index = (streak_day - 1) % len(DAILY_LADDER_REWARDS)
        base_amount = DAILY_LADDER_REWARDS[ladder_index]
        milestone_bonus = STREAK_MILESTONE_REWARDS.get(streak_day, 0)
        total_amount = base_amount + milestone_bonus
        freeze_tokens = STREAK_FREEZE_TOKEN_MILESTONES.get(streak_day, 0)

        await self.adjust(
            user_id=user_id,
            amount=total_amount,
            reason=CurrencyTransactionType.streak_bonus,
            context=f"checkin:{now.date().isoformat()}",
            metadata={
                "daily_checkin": True,
                "base_amount": base_amount,
                "milestone_bonus": milestone_bonus,
                "current_streak": streak_day,
                "daily_ladder_day": ladder_index + 1,
                "daily_ladder_rewards": list(DAILY_LADDER_REWARDS),
                "freeze_tokens_granted": freeze_tokens,
            },
            now=now,
        )
        if freeze_tokens > 0:
            await self._repo.add_streak_freeze_tokens(user_id, freeze_tokens)
