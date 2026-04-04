import uuid
from datetime import datetime, timedelta, timezone

from app.infrastructure.db.models import CurrencyTransactionType, StoreItemKind, User
from app.modules.analytics.model.analytics import AnalyticsEventName
from app.modules.analytics.service.analytics_service import AnalyticsService
from app.modules.economy.model.wallet import (
    CurrencyTransactionRead,
    WalletBenefitRead,
    WalletEconomyConfigRead,
    WalletGoalRead,
    WalletLockedRewardRead,
    WalletPurchaseRead,
    WalletRead,
    WalletStreakMilestoneRead,
)
from app.modules.economy.config.tuning import (
    DAILY_LADDER_REWARDS,
    GOAL_WINDOW_DAYS,
    HOARDER_GOAL_INITIAL_TARGET,
    HOARDER_GOAL_NEXT_TARGET,
    INACTIVE_GOAL_INITIAL_TARGET,
    INACTIVE_GOAL_NEXT_TARGET,
    NEAR_MISS_MAX_DELTA,
    SPENDER_GOAL_INITIAL_TARGET,
    SPENDER_GOAL_NEXT_TARGET,
    STREAK_FREEZE_TOKEN_MILESTONES,
    STREAK_MILESTONE_REWARDS,
)
from app.modules.economy.repository.store_repository import StoreRepository
from app.modules.economy.repository.wallet_repository import WalletRepository


class WalletService:
    def __init__(
        self,
        repo: WalletRepository,
        store_repo: StoreRepository | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._repo = repo
        self._store_repo = store_repo
        self._analytics = analytics

    async def ensure_wallet(self, user_id: uuid.UUID) -> None:
        await self._repo.ensure_balance_row(user_id)

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

    async def _active_benefits(self, user: User, *, premium_unlock_until: datetime | None = None) -> list[WalletBenefitRead]:
        benefits: list[WalletBenefitRead] = []

        effective_unlock_until = premium_unlock_until if premium_unlock_until is not None else user.premium_unlock_until
        if effective_unlock_until is not None:
            unlock_until = (
                effective_unlock_until
                if effective_unlock_until.tzinfo is not None
                else effective_unlock_until.replace(tzinfo=timezone.utc)
            )
            if unlock_until > datetime.now(timezone.utc):
                benefits.append(
                    WalletBenefitRead(
                        key="premium_access",
                        kind="premium_access",
                        metadata={"source": "wallet_unlock"},
                        expires_at=unlock_until,
                    )
                )

        if self._store_repo is None:
            return benefits

        recent_purchases = await self._store_repo.list_recent_purchases(user.id, limit=10)
        seen_codes: set[str] = set()
        seen_unlocks: set[str] = set()
        seen_starters: set[str] = set()
        for purchase in recent_purchases:
            item = purchase.item
            if item is None or purchase.meta is None:
                continue
            discount_code = purchase.meta.get("discount_code")
            if item.kind.value in {"starter", "subscription_discount"} and isinstance(discount_code, str) and discount_code not in seen_codes:
                seen_codes.add(discount_code)
                benefits.append(
                    WalletBenefitRead(
                        key=f"discount_code:{discount_code}",
                        kind=item.kind.value,
                        metadata={
                            "code": discount_code,
                            "discount_percent": purchase.meta.get("discount_percent"),
                            "item_slug": item.slug,
                            "item_title": item.title,
                        },
                        expires_at=None,
                    )
                )
            if item.kind.value == "starter" and not isinstance(discount_code, str):
                starter_key = item.slug
                if starter_key in seen_starters:
                    continue
                seen_starters.add(starter_key)
                benefits.append(
                    WalletBenefitRead(
                        key=f"starter:{starter_key}",
                        kind="starter",
                        metadata={
                            "item_slug": item.slug,
                            "item_title": item.title,
                            "reward_title": purchase.meta.get("reward_title"),
                            "reward_body": purchase.meta.get("reward_body"),
                            "starter_type": purchase.meta.get("starter_type"),
                        },
                        expires_at=None,
                    )
                )
            if item.kind.value in {"premium_prompt_unlock", "prompt_bundle"}:
                unlock_key = item.slug
                if unlock_key in seen_unlocks:
                    continue
                seen_unlocks.add(unlock_key)
                benefits.append(
                    WalletBenefitRead(
                        key=f"prompt_unlock:{unlock_key}",
                        kind=item.kind.value,
                        metadata={
                            "item_slug": item.slug,
                            "item_title": item.title,
                            "prompt_title": purchase.meta.get("prompt_title"),
                            "prompt_titles": purchase.meta.get("prompt_titles"),
                        },
                        expires_at=None,
                    )
                )

        active_boosts = await self._repo.list_active_boosts(user_id=user.id)
        for boost in active_boosts:
            boost_meta = boost.meta if isinstance(boost.meta, dict) else {}
            missions_total = max(0, int(boost.missions_total))
            missions_used = max(0, int(boost.missions_used))
            missions_left = max(0, missions_total - missions_used)
            benefits.append(
                WalletBenefitRead(
                    key=f"boost:{boost.id}",
                    kind="boost",
                    metadata={
                        **boost_meta,
                        "boost_pct": int(boost.boost_percent),
                        "boost_missions_total": missions_total,
                        "boost_missions_left": missions_left,
                    },
                    expires_at=boost.expires_at,
                )
            )
        return benefits

    async def _build_goals(
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
        goals = await self._build_goals(
            user=user,
            balance=int(balance_row.balance),
            current_streak=int(balance_row.current_streak),
            spend_streak_days=spend_streak_days,
            rank_points=rank_points,
            rank_level=rank_level,
            rank_next_threshold=rank_next_threshold,
        )
        if self._analytics is not None:
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
            active_benefits=await self._active_benefits(user, premium_unlock_until=premium_unlock_until),
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
