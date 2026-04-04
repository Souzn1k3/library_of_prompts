from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from app.infrastructure.db.models import (
    CurrencyTransactionType,
    LessonMission,
    MissionActionType,
    User,
)
from app.modules.economy.config.tuning import (
    ANTI_FARM_BREAKPOINTS,
    ANTI_FARM_FALLBACK_FACTOR,
    MISSION_DAILY_EARN_CAP,
    STREAK_SURPRISE_HIT_CHANCE_PERCENT,
    STREAK_SURPRISE_PITY_THRESHOLD,
)
from app.modules.economy.repository.wallet_repository import WalletRepository


class MissionRewardPlanner:
    def __init__(self, wallet_repo: WalletRepository | None) -> None:
        self._wallet_repo = wallet_repo

    def _mission_category(self, mission: LessonMission, *, event_type: str) -> str:
        if mission.action_type in {
            MissionActionType.copy_prompt,
            MissionActionType.save_prompt,
            MissionActionType.copy_or_save_prompt,
            MissionActionType.apply_prompt,
        }:
            return "prompt"
        if mission.action_type == MissionActionType.lesson_completed:
            return "learning"
        if mission.action_type in {
            MissionActionType.daily_checkin,
            MissionActionType.streak_activity,
        }:
            return "habit"
        if mission.action_type == MissionActionType.store_purchase or event_type == "store_purchase":
            return "spend"
        return "progress"

    def _anti_farm_factor(self, same_day_count: int) -> float:
        for threshold, factor in ANTI_FARM_BREAKPOINTS:
            if same_day_count <= threshold:
                return factor
        return ANTI_FARM_FALLBACK_FACTOR

    def _day_bounds(self, now: datetime) -> tuple[datetime, datetime]:
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        return start, start + timedelta(days=1)

    def _daily_cap_for_rank(self, rank_level: int) -> int:
        allowance = min(10, max(0, rank_level - 1))
        return MISSION_DAILY_EARN_CAP + allowance

    def _surprise_hit(self, *, seed: str, pity_count: int) -> bool:
        if pity_count >= STREAK_SURPRISE_PITY_THRESHOLD:
            return True
        digest = int(sha256(seed.encode("utf-8")).hexdigest(), 16)
        return digest % 100 < STREAK_SURPRISE_HIT_CHANCE_PERCENT

    async def build_reward_plan(
        self,
        *,
        user: User,
        mission: LessonMission,
        event_type: str,
        base_credits: int,
        source_key: str,
        include_chain_bonus: bool,
        segment: str,
        now: datetime,
    ) -> dict[str, Any]:
        base_credits = max(0, int(base_credits))
        if self._wallet_repo is None or base_credits <= 0:
            return {
                "base_reward": base_credits,
                "spend_bonus": 0,
                "chain_bonus": 0,
                "surprise_bonus": 0,
                "components": {
                    "base_credits": base_credits,
                    "anti_farm_factor": 1.0,
                    "synergy_bonus": 0,
                    "boost_mult": 1.0,
                    "catchup_mult": 1.0,
                    "catchup_boost_pct": 0,
                    "catchup_activated": False,
                    "spend_streak_mult": 1.0,
                    "daily_cap": MISSION_DAILY_EARN_CAP,
                    "daily_earned_before": 0,
                    "daily_earned_available": MISSION_DAILY_EARN_CAP,
                    "owned_value_delta": 0,
                },
            }

        day_start, day_end = self._day_bounds(now)
        same_day_count = await self._wallet_repo.count_mission_events_since(
            user_id=user.id,
            mission_id=mission.id,
            since=day_start,
        )
        anti_farm_factor = self._anti_farm_factor(same_day_count)
        mission_category = self._mission_category(mission, event_type=event_type)
        synergy_bonus = await self._wallet_repo.owned_synergy_bonus(
            user_id=user.id,
            mission_category=mission_category,
        )
        balance_row = await self._wallet_repo.get_balance_row(user.id, for_update=True)
        spend_streak_mult = self._wallet_repo.spend_streak_multiplier(int(balance_row.spend_streak_days))
        catchup_mult, catchup_boost_pct, catchup_activated = await self._wallet_repo.resolve_catchup_boost(
            user_id=user.id,
            segment=segment,
            now=now,
        )
        boost_mult, boost_pct, boost_missions_left = await self._wallet_repo.consume_active_boost(
            user_id=user.id,
            now=now,
        )
        total_boost_mult = boost_mult * catchup_mult

        pity_count = int(balance_row.surprise_miss_streak)
        surprise_seed = f"{source_key}:{mission.slug}:{base_credits}:{same_day_count}"
        surprise_hit = self._surprise_hit(seed=surprise_seed, pity_count=pity_count)
        surprise_roll_bonus = 0
        if surprise_hit:
            surprise_roll_bonus = 2 + min(4, max(0, int(balance_row.rank_level) - 1) // 2)
            balance_row.surprise_miss_streak = 0
        else:
            balance_row.surprise_miss_streak = pity_count + 1

        chain_bonus = int(mission.chain_bonus_credits) if include_chain_bonus else 0
        base_component = max(0, int(base_credits * anti_farm_factor + synergy_bonus))
        boosted_component = max(0, int(base_component * total_boost_mult))
        spend_bonus_component = max(0, int(boosted_component * max(spend_streak_mult - 1.0, 0.0)))
        composed_total = boosted_component + spend_bonus_component + chain_bonus + surprise_roll_bonus

        catchup_only_component = max(0, int(base_component * catchup_mult))
        owned_boost_delta = max(0, boosted_component - catchup_only_component)
        owned_value_delta = max(0, int(synergy_bonus)) + owned_boost_delta
        if owned_value_delta > 0:
            balance_row.owned_value_generated = int(balance_row.owned_value_generated) + owned_value_delta

        daily_cap = self._daily_cap_for_rank(int(balance_row.rank_level))
        earned_today_before = await self._wallet_repo.sum_mission_earnings_today(
            user_id=user.id,
            start_of_day=day_start,
            end_of_day=day_end,
        )
        available_today = max(0, daily_cap - earned_today_before)
        capped_total = min(composed_total, available_today)

        remaining = capped_total
        base_reward = min(boosted_component, remaining)
        remaining -= base_reward
        spend_bonus = min(spend_bonus_component, remaining)
        remaining -= spend_bonus
        chain_award = min(chain_bonus, remaining)
        remaining -= chain_award
        surprise_award = max(0, remaining)

        return {
            "base_reward": max(0, base_reward),
            "spend_bonus": max(0, spend_bonus),
            "chain_bonus": max(0, chain_award),
            "surprise_bonus": max(0, surprise_award),
            "components": {
                "base_credits": base_credits,
                "anti_farm_factor": anti_farm_factor,
                "same_day_count": same_day_count,
                "mission_category": mission_category,
                "synergy_bonus": synergy_bonus,
                "boost_mult": round(boost_mult, 4),
                "boost_pct": boost_pct,
                "boost_missions_left": boost_missions_left,
                "catchup_mult": round(catchup_mult, 4),
                "catchup_boost_pct": catchup_boost_pct,
                "catchup_activated": catchup_activated,
                "spend_streak_mult": round(spend_streak_mult, 4),
                "daily_cap": daily_cap,
                "daily_earned_before": earned_today_before,
                "daily_earned_available": available_today,
                "pre_cap_total": composed_total,
                "post_cap_total": capped_total,
                "pity_before": pity_count,
                "surprise_hit": surprise_hit,
                "surprise_roll_bonus": surprise_roll_bonus,
                "chain_bonus_configured": chain_bonus,
                "owned_value_delta": owned_value_delta,
            },
        }

    async def grant_reward_extras(
        self,
        *,
        user: User,
        mission: LessonMission,
        source_id: uuid.UUID,
        cycle_number: int,
        now: datetime,
        source_context: str,
        plan: dict[str, Any],
    ) -> int:
        if self._wallet_repo is None:
            return int(plan.get("base_reward", 0) or 0)

        total_awarded = int(plan.get("base_reward", 0) or 0)
        components = dict(plan.get("components") or {})
        for key, reason in (
            ("spend_bonus", CurrencyTransactionType.spend_streak_bonus),
            ("chain_bonus", CurrencyTransactionType.rank_bonus),
            ("surprise_bonus", CurrencyTransactionType.surprise_reward),
        ):
            amount = int(plan.get(key, 0) or 0)
            if amount <= 0:
                continue
            total_awarded += amount
            await self._wallet_repo.adjust_balance(
                user_id=user.id,
                amount=amount,
                reason=reason,
                context=f"{source_context}:{key}:cycle:{cycle_number}",
                source_id=source_id,
                metadata={
                    "mission_id": str(mission.id),
                    "mission_slug": mission.slug,
                    "reward_cycle": cycle_number,
                    "reward_component": key,
                    **components,
                },
                now=now,
            )
        return total_awarded
