from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.infrastructure.db.models import User
from app.modules.economy.config.tuning import (
    GOAL_WINDOW_DAYS,
    HOARDER_GOAL_INITIAL_TARGET,
    HOARDER_GOAL_NEXT_TARGET,
    INACTIVE_GOAL_INITIAL_TARGET,
    INACTIVE_GOAL_NEXT_TARGET,
    SPENDER_GOAL_INITIAL_TARGET,
    SPENDER_GOAL_NEXT_TARGET,
)
from app.modules.economy.model.wallet import WalletGoalRead
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository


class WalletGoalPlanner:
    def __init__(self, repo: WalletRepository, store_repo: StoreRepository | None = None) -> None:
        self._repo = repo
        self._store_repo = store_repo

    async def build_goals(
        self,
        *,
        user: User,
        balance: int,
        current_streak: int,
        spend_streak_days: int,
        rank_points: int,
        rank_level: int,
        rank_next_threshold: int,
    ) -> list[WalletGoalRead]:
        goals: list[WalletGoalRead] = []

        if self._store_repo is not None:
            items = await self._store_repo.list_active_items()
            owned_ids = await self._store_repo.list_owned_one_time_item_ids(user.id)
            candidates = [
                item
                for item in items
                if item.is_active and (item.availability is None or item.availability > 0) and item.id not in owned_ids
            ]
            if candidates:
                near_locked = [item for item in candidates if item.price > balance]
                if near_locked:
                    next_item = min(near_locked, key=lambda row: (row.price - balance, row.price, row.slug))
                    goals.append(
                        WalletGoalRead(
                            layer="short",
                            key=f"next-item:{next_item.slug}",
                            title=f"Next unlock: {next_item.title}",
                            description="Reach the next purchase threshold and keep your spend loop alive.",
                            progress=min(balance, max(1, int(next_item.price))),
                            target=max(1, int(next_item.price)),
                            reward="Immediate purchase unlock",
                            expires_at=None,
                        )
                    )
                else:
                    next_item = min(candidates, key=lambda row: (row.price, row.slug))
                    goals.append(
                        WalletGoalRead(
                            layer="short",
                            key=f"buy-now:{next_item.slug}",
                            title=f"Spend now: {next_item.title}",
                            description="Trigger the spend -> reward loop with a purchase you can afford now.",
                            progress=0,
                            target=1,
                            reward="Cashback + streak momentum",
                            expires_at=None,
                        )
                    )

        if not goals:
            goals.append(
                WalletGoalRead(
                    layer="short",
                    key="next-earn",
                    title="Earn 5 LMN",
                    description="Complete one more action cycle to open affordable offers.",
                    progress=min(balance, 5),
                    target=5,
                    reward="Store availability",
                )
            )

        segment = await self._repo.classify_user_segment(user_id=user.id)
        if segment == "inactive":
            mid_target = INACTIVE_GOAL_INITIAL_TARGET
            mid_progress = min(current_streak, mid_target)
            if mid_progress >= mid_target:
                mid_target = INACTIVE_GOAL_NEXT_TARGET
                mid_progress = min(current_streak, mid_target)
            goals.append(
                WalletGoalRead(
                    layer="mid",
                    key=f"inactive-comeback:{mid_target}",
                    title=f"Comeback streak {mid_target} days",
                    description="Complete a short comeback bundle to activate temporary boosted rewards.",
                    progress=mid_progress,
                    target=mid_target,
                    reward="48h comeback boost",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=GOAL_WINDOW_DAYS),
                )
            )
        elif segment == "hoarder":
            mid_target = HOARDER_GOAL_INITIAL_TARGET
            mid_progress = min(spend_streak_days, mid_target)
            if mid_progress >= mid_target:
                mid_target = HOARDER_GOAL_NEXT_TARGET
                mid_progress = min(spend_streak_days, mid_target)
            goals.append(
                WalletGoalRead(
                    layer="mid",
                    key=f"hoarder-convert:{mid_target}",
                    title=f"Spend {mid_target} days in a row",
                    description="Convert saved LMN into active progression power.",
                    progress=mid_progress,
                    target=mid_target,
                    reward="Booster unlock track",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=GOAL_WINDOW_DAYS),
                )
            )
        elif segment == "spender":
            mid_target = SPENDER_GOAL_INITIAL_TARGET
            mid_progress = min(spend_streak_days, mid_target)
            if mid_progress >= mid_target:
                mid_target = SPENDER_GOAL_NEXT_TARGET
                mid_progress = min(spend_streak_days, mid_target)
            goals.append(
                WalletGoalRead(
                    layer="mid",
                    key=f"spender-maintain:{mid_target}",
                    title=f"Maintain {mid_target}-day spend streak",
                    description="Keep the multiplier hot for stronger mission rewards.",
                    progress=mid_progress,
                    target=mid_target,
                    reward="Higher spend multiplier",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=GOAL_WINDOW_DAYS),
                )
            )
        else:
            mid_target = 7 if current_streak >= 3 else 3
            mid_progress = min(current_streak, mid_target)
            if mid_progress >= mid_target:
                mid_target = 14 if mid_target < 14 else mid_target + 7
                mid_progress = min(current_streak, mid_target)
            goals.append(
                WalletGoalRead(
                    layer="mid",
                    key=f"habit-window:{mid_target}",
                    title=f"Reach {mid_target}-day activity streak",
                    description="Keep returning daily to unlock milestone rewards and freeze tokens.",
                    progress=mid_progress,
                    target=mid_target,
                    reward="Streak milestone reward",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=GOAL_WINDOW_DAYS),
                )
            )

        goals.append(
            WalletGoalRead(
                layer="long",
                key=f"rank:{rank_level + 1}",
                title=f"Vault Rank {rank_level + 1}",
                description="Earn and spend LMN to unlock stronger offers and bonuses.",
                progress=rank_points,
                target=max(rank_points + 1, rank_next_threshold),
                reward="Rank unlocks",
            )
        )

        return goals
