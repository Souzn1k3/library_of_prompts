from __future__ import annotations

from datetime import datetime, timezone

from app.modules.economy.config.tuning import (
    DAILY_LADDER_REWARDS,
    NEAR_MISS_MAX_DELTA,
    STREAK_MILESTONE_REWARDS,
)
from app.modules.economy.model.wallet import WalletEconomyConfigRead, WalletStreakMilestoneRead


class WalletSupportMixin:
    def _can_check_in(self, last_check_in_at: datetime | None) -> bool:
        if last_check_in_at is None:
            return True
        current = last_check_in_at if last_check_in_at.tzinfo is not None else last_check_in_at.replace(tzinfo=timezone.utc)
        return current.astimezone(timezone.utc).date() < datetime.now(timezone.utc).date()

    def _economy_config_projection(self) -> WalletEconomyConfigRead:
        milestones = [
            WalletStreakMilestoneRead(streak=streak, reward=reward)
            for streak, reward in sorted(STREAK_MILESTONE_REWARDS.items())
        ]
        return WalletEconomyConfigRead(
            daily_ladder_rewards=list(DAILY_LADDER_REWARDS),
            streak_milestones=milestones,
            near_miss_max_delta=NEAR_MISS_MAX_DELTA,
        )
