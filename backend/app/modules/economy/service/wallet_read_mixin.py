from __future__ import annotations

from app.infrastructure.db.models import StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.economy.model.wallet import (
    CurrencyTransactionRead,
    WalletLockedRewardRead,
    WalletPurchaseRead,
    WalletRead,
)


class WalletReadMixin:
    async def _emit_goal_completed_events(self, *, user: User, goals: list[object]) -> None:
        if self._analytics is None:
            return
        for goal in goals:
            if int(goal.target) <= 0 or int(goal.progress) < int(goal.target):
                continue
            await self._analytics.record_server_event(
                event_name=AnalyticsEventName.goal_completed,
                user_id=user.id,
                metadata={
                    "goal_layer": goal.layer,
                    "goal_key": goal.key,
                    "goal_target": int(goal.target),
                    "goal_progress": int(goal.progress),
                },
                context_page="/api/v1/wallet",
                context_feature="goal_progression",
                event_id=f"goal_completed:{user.id}:{goal.key}:{goal.target}",
            )

    async def get_wallet(self, user: User, *, limit: int = 20) -> WalletRead:
        balance_row = await self._repo.get_balance_row(user.id)
        premium_unlock_until = await self._repo.get_premium_unlock_until(user.id)
        recent = await self._repo.list_recent_transactions(user.id, limit=limit)
        recent_purchases = (
            await self._store_repo.list_recent_purchases(user.id, limit=8)
            if self._store_repo is not None
            else []
        )
        pending_locked_rewards = await self._repo.list_pending_locked_rewards(user.id)
        rank_points, rank_level, rank_next_threshold = await self._repo.get_rank_snapshot(user.id)
        spend_streak_days = int(balance_row.spend_streak_days)
        goals = await self._goal_planner.build_goals(
            user=user,
            balance=int(balance_row.balance),
            current_streak=int(balance_row.current_streak),
            spend_streak_days=spend_streak_days,
            rank_points=rank_points,
            rank_level=rank_level,
            rank_next_threshold=rank_next_threshold,
        )
        await self._emit_goal_completed_events(user=user, goals=goals)

        return WalletRead(
            balance=int(balance_row.balance),
            currency="LMN",
            currency_name="Lumens",
            currency_symbol="LMN",
            total_earned=int(balance_row.total_earned),
            total_spent=int(balance_row.total_spent),
            current_streak=int(balance_row.current_streak),
            best_streak=int(balance_row.best_streak),
            spend_streak_days=spend_streak_days,
            spend_streak_mult=self._repo.spend_streak_multiplier(spend_streak_days),
            streak_freeze_tokens=int(balance_row.streak_freeze_tokens),
            last_check_in_at=balance_row.last_check_in_at,
            check_in_available=self._can_check_in(balance_row.last_check_in_at),
            pending_locked_rewards=[
                WalletLockedRewardRead(
                    id=row.id,
                    amount=int(row.amount),
                    status=row.status,
                    required_mission_count=int(row.required_mission_count),
                    completed_mission_count=int(row.completed_mission_count),
                    unlock_by=row.unlock_by,
                    created_at=row.created_at,
                    metadata=row.meta,
                )
                for row in pending_locked_rewards
            ],
            rank_points=rank_points,
            rank_level=rank_level,
            rank_next_threshold=rank_next_threshold,
            owned_value_generated=int(balance_row.owned_value_generated),
            goals=goals,
            economy_config=self._economy_config_projection(),
            premium_unlock_until=premium_unlock_until,
            active_benefits=await self._benefit_resolver.active_benefits(
                user,
                premium_unlock_until=premium_unlock_until,
            ),
            recent_purchases=[
                WalletPurchaseRead(
                    id=row.id,
                    item_slug=row.item.slug if row.item is not None else "",
                    item_title=row.item.title if row.item is not None else "",
                    kind=row.item.kind if row.item is not None else StoreItemKind.future,
                    price_paid=row.price_paid,
                    status=row.status,
                    metadata=row.meta,
                    created_at=row.created_at,
                )
                for row in recent_purchases
                if row.item is not None
            ],
            recent=[
                CurrencyTransactionRead(
                    id=row.id,
                    amount=row.amount,
                    balance_after=row.balance_after,
                    reason=row.reason,
                    context=row.context,
                    metadata=row.meta,
                    created_at=row.created_at,
                )
                for row in recent
            ],
        )
