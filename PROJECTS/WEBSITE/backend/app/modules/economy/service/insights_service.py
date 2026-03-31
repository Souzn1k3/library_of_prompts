from __future__ import annotations

import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.modules.economy.model.insights import (
    EconomyArmKpiRead,
    EconomyExperimentKpiRead,
    EconomyGuardrailRead,
    EconomyTuningRead,
)
from app.modules.economy.repository.insights_repository import EconomyInsightsRepository
from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_NAME,
    economy_experiment_variant,
)


SOURCE_REASONS = {
    "mission_reward",
    "streak_bonus",
    "first_purchase_bonus",
    "surprise_reward",
    "cashback_unlocked",
    "rank_bonus",
    "spend_streak_bonus",
}
SINK_REASONS = {"store_purchase", "boost_purchase", "upgrade_purchase"}


class EconomyInsightsService:
    def __init__(self, repo: EconomyInsightsRepository) -> None:
        self._repo = repo

    def _round(self, value: float | None) -> float | None:
        if value is None:
            return None
        return round(float(value), 4)

    def _retention_ratio(
        self,
        *,
        first_activity: dict[uuid.UUID, datetime.date],
        activity_days: dict[uuid.UUID, set[datetime.date]],
        offset_days: int,
        end_date: datetime.date,
        users: set[uuid.UUID],
    ) -> float:
        eligible: list[uuid.UUID] = []
        retained = 0
        for user_id in users:
            first_day = first_activity.get(user_id)
            if first_day is None:
                continue
            if first_day + timedelta(days=offset_days) > end_date:
                continue
            eligible.append(user_id)
            if (first_day + timedelta(days=offset_days)) in activity_days.get(user_id, set()):
                retained += 1
        if not eligible:
            return 0.0
        return retained / len(eligible)

    def _arm_kpis(
        self,
        *,
        users: set[uuid.UUID],
        purchases_by_user: dict[uuid.UUID, list[datetime]],
        activity_days: dict[uuid.UUID, set[datetime.date]],
        first_activity: dict[uuid.UUID, datetime.date],
        tx_by_user: dict[uuid.UUID, list[tuple[int, str]]],
        offer_views_by_user: dict[uuid.UUID, int],
        offer_conversions_by_user: dict[uuid.UUID, int],
        goals_completed_users: set[uuid.UUID],
        wallet_rows: dict[uuid.UUID, tuple[int, int, int, int]],
        end_date: datetime.date,
    ) -> EconomyArmKpiRead:
        spenders = [user_id for user_id in users if purchases_by_user.get(user_id)]
        repeat_spenders = [user_id for user_id in spenders if len(purchases_by_user.get(user_id, [])) >= 2]
        repeat_rate = (len(repeat_spenders) / len(spenders)) if spenders else 0.0
        total_purchases = sum(len(purchases_by_user.get(user_id, [])) for user_id in users)
        spend_frequency = (total_purchases / len(spenders)) if spenders else 0.0

        second_purchase_hours: list[float] = []
        for user_id in users:
            user_purchases = purchases_by_user.get(user_id, [])
            if len(user_purchases) < 2:
                continue
            delta = user_purchases[1] - user_purchases[0]
            second_purchase_hours.append(delta.total_seconds() / 3600.0)
        median_second = statistics.median(second_purchase_hours) if second_purchase_hours else None

        d1 = self._retention_ratio(
            first_activity=first_activity,
            activity_days=activity_days,
            offset_days=1,
            end_date=end_date,
            users=users,
        )
        d7 = self._retention_ratio(
            first_activity=first_activity,
            activity_days=activity_days,
            offset_days=7,
            end_date=end_date,
            users=users,
        )
        d14 = self._retention_ratio(
            first_activity=first_activity,
            activity_days=activity_days,
            offset_days=14,
            end_date=end_date,
            users=users,
        )

        source_sum = 0
        sink_sum = 0
        for user_id in users:
            for amount, reason in tx_by_user.get(user_id, []):
                if reason in SOURCE_REASONS and amount > 0:
                    source_sum += amount
                elif reason in SINK_REASONS and amount < 0:
                    sink_sum += abs(amount)
        circulation_ratio = (sink_sum / source_sum) if source_sum > 0 else 0.0

        offer_views = sum(offer_views_by_user.get(user_id, 0) for user_id in users)
        offer_conversions = sum(offer_conversions_by_user.get(user_id, 0) for user_id in users)
        offer_conversion = (offer_conversions / offer_views) if offer_views > 0 else 0.0

        streak_population = 0
        streak_survived = 0
        for user_id in users:
            row = wallet_rows.get(user_id)
            if row is None:
                continue
            current_streak = int(row[0])
            if current_streak >= 1:
                streak_population += 1
                if current_streak >= 3:
                    streak_survived += 1
        streak_survival = (streak_survived / streak_population) if streak_population > 0 else 0.0

        goal_completion_rate = (
            len([user_id for user_id in users if user_id in goals_completed_users]) / len(users)
            if users
            else 0.0
        )

        return EconomyArmKpiRead(
            variant="",
            users=len(users),
            repeat_purchase_rate=self._round(repeat_rate) or 0.0,
            spend_frequency=self._round(spend_frequency) or 0.0,
            median_time_to_second_purchase_hours=self._round(median_second),
            d1_retention=self._round(d1) or 0.0,
            d7_retention=self._round(d7) or 0.0,
            d14_retention=self._round(d14) or 0.0,
            lmn_circulation_ratio=self._round(circulation_ratio) or 0.0,
            offer_conversion=self._round(offer_conversion) or 0.0,
            streak_survival=self._round(streak_survival) or 0.0,
            goal_completion_rate=self._round(goal_completion_rate) or 0.0,
        )

    async def experiment_kpis(self, *, window_days: int = 14) -> EconomyExperimentKpiRead:
        now = datetime.now(timezone.utc)
        start_at = now - timedelta(days=max(1, window_days))
        end_at = now
        end_date = now.date()

        purchases = await self._repo.list_purchases(start_at=start_at, end_at=end_at)
        mission_events = await self._repo.list_mission_events(start_at=start_at, end_at=end_at)
        tx_rows = await self._repo.list_currency_transactions(start_at=start_at, end_at=end_at)
        wallet_rows_raw = await self._repo.list_wallet_rows()
        analytics_rows = await self._repo.list_analytics_events(
            start_at=start_at,
            end_at=end_at,
            event_names=[
                "store_offer_viewed",
                "store_purchase_completed",
                "goal_completed",
            ],
        )

        purchases_by_user: dict[uuid.UUID, list[datetime]] = defaultdict(list)
        activity_days: dict[uuid.UUID, set[datetime.date]] = defaultdict(set)
        first_activity: dict[uuid.UUID, datetime.date] = {}
        for user_id, created_at in purchases:
            purchases_by_user[user_id].append(created_at)
            day = created_at.astimezone(timezone.utc).date()
            activity_days[user_id].add(day)
            first_activity[user_id] = min(first_activity.get(user_id, day), day)
        for user_id, created_at in mission_events:
            day = created_at.astimezone(timezone.utc).date()
            activity_days[user_id].add(day)
            first_activity[user_id] = min(first_activity.get(user_id, day), day)

        tx_by_user: dict[uuid.UUID, list[tuple[int, str]]] = defaultdict(list)
        for user_id, amount, reason, _created_at in tx_rows:
            tx_by_user[user_id].append((amount, reason))

        wallet_rows: dict[uuid.UUID, tuple[int, int, int, int]] = {}
        payer_status_by_user: dict[uuid.UUID, str] = {}
        for user_id, current_streak, balance, rank_level, total_spent in wallet_rows_raw:
            wallet_rows[user_id] = (current_streak, balance, rank_level, total_spent)
            payer_status_by_user[user_id] = "payer" if total_spent > 0 else "non_payer"

        offer_views_by_user: dict[uuid.UUID, int] = defaultdict(int)
        offer_conversions_by_user: dict[uuid.UUID, int] = defaultdict(int)
        goals_completed_users: set[uuid.UUID] = set()
        for user_id, event_name, metadata, _occurred_at in analytics_rows:
            if user_id is None:
                continue
            if event_name == "store_offer_viewed":
                offer_views_by_user[user_id] += 1
            elif event_name == "store_purchase_completed":
                if bool((metadata or {}).get("is_limited_offer")) or bool((metadata or {}).get("is_dynamic_offer")):
                    offer_conversions_by_user[user_id] += 1
            elif event_name == "goal_completed":
                goals_completed_users.add(user_id)

        active_users = set(activity_days.keys()) | set(purchases_by_user.keys()) | set(tx_by_user.keys())
        variant_users: dict[str, set[uuid.UUID]] = {"control": set(), "treatment": set()}
        for user_id in active_users:
            payer_status = payer_status_by_user.get(user_id, "non_payer")
            variant = economy_experiment_variant(user_id=user_id, payer_status=payer_status)
            variant_users[variant].add(user_id)

        arms: list[EconomyArmKpiRead] = []
        for variant in ("control", "treatment"):
            metrics = self._arm_kpis(
                users=variant_users.get(variant, set()),
                purchases_by_user=purchases_by_user,
                activity_days=activity_days,
                first_activity=first_activity,
                tx_by_user=tx_by_user,
                offer_views_by_user=offer_views_by_user,
                offer_conversions_by_user=offer_conversions_by_user,
                goals_completed_users=goals_completed_users,
                wallet_rows=wallet_rows,
                end_date=end_date,
            )
            metrics.variant = variant
            arms.append(metrics)

        control = next((arm for arm in arms if arm.variant == "control"), None)
        treatment = next((arm for arm in arms if arm.variant == "treatment"), None)
        retention_drop_flag = bool(
            control and treatment and (treatment.d7_retention + 0.03) < control.d7_retention
        )
        inflation_breach_flag = bool(treatment and treatment.lmn_circulation_ratio < 0.45)

        mission_events_per_user: dict[str, float] = {}
        for variant, users in variant_users.items():
            if not users:
                mission_events_per_user[variant] = 0.0
                continue
            mission_count = len([1 for user_id, _created_at in mission_events if user_id in users])
            mission_events_per_user[variant] = mission_count / len(users)
        mission_completion_collapse_flag = (
            mission_events_per_user.get("control", 0.0) > 0
            and mission_events_per_user.get("treatment", 0.0)
            < (mission_events_per_user.get("control", 0.0) * 0.8)
        )
        decision_ready = bool(
            window_days >= 14
            and control is not None
            and treatment is not None
            and control.users >= 50
            and treatment.users >= 50
        )
        guardrails_pass = not any(
            (
                retention_drop_flag,
                inflation_breach_flag,
                mission_completion_collapse_flag,
            )
        )
        if not decision_ready:
            next_step = "continue_ab_test_until_minimum_runtime"
        elif guardrails_pass:
            next_step = "pass_guardrails_stage_ramp_50_to_100"
        else:
            next_step = "hold_rollout_and_tune_economy"

        return EconomyExperimentKpiRead(
            experiment_name=ECONOMY_EXPERIMENT_NAME,
            generated_at=now,
            window_days=window_days,
            arms=arms,
            guardrails=EconomyGuardrailRead(
                retention_drop_flag=retention_drop_flag,
                inflation_breach_flag=inflation_breach_flag,
                mission_completion_collapse_flag=mission_completion_collapse_flag,
            ),
            is_decision_ready=decision_ready,
            recommended_next_step=next_step,
        )

    async def weekly_tuning(self, *, window_days: int = 7) -> EconomyTuningRead:
        now = datetime.now(timezone.utc)
        start_at = now - timedelta(days=max(1, window_days))
        tx_rows = await self._repo.list_currency_transactions(start_at=start_at, end_at=now)
        wallet_rows = await self._repo.list_wallet_rows()

        source_sum = 0
        sink_sum = 0
        for _user_id, amount, reason, _created_at in tx_rows:
            if reason in SOURCE_REASONS and amount > 0:
                source_sum += amount
            elif reason in SINK_REASONS and amount < 0:
                sink_sum += abs(amount)
        circulation_ratio = (sink_sum / source_sum) if source_sum > 0 else 0.0

        balances = [balance for _user_id, _streak, balance, _rank, _spent in wallet_rows]
        median_idle_balance = statistics.median(balances) if balances else 0.0

        inflation_triggered = circulation_ratio < 0.55 or median_idle_balance > 60
        if circulation_ratio < 0.45 or median_idle_balance > 90:
            inflation_risk = "high"
        elif inflation_triggered:
            inflation_risk = "medium"
        else:
            inflation_risk = "low"

        recommendation_flags: list[str] = []
        if circulation_ratio < 0.55:
            recommendation_flags.append("low_circulation_ratio")
        if median_idle_balance > 60:
            recommendation_flags.append("idle_balance_above_band")
        if circulation_ratio < 0.45:
            recommendation_flags.append("tighten_mission_sources_10pct")
        if median_idle_balance > 75:
            recommendation_flags.append("increase_upgrade_sink_pressure")
        zero_streak_users = len([1 for _uid, streak, _bal, _rank, _spent in wallet_rows if streak <= 0])
        if wallet_rows and (zero_streak_users / len(wallet_rows)) > 0.35:
            recommendation_flags.append("expand_comeback_bundle_boost")
        if not recommendation_flags:
            recommendation_flags.append("economy_stable_keep_balanced")

        return EconomyTuningRead(
            computed_at=now,
            window_days=window_days,
            circulation_ratio_7d=round(circulation_ratio, 4),
            median_idle_balance=round(float(median_idle_balance), 2),
            inflation_triggered=inflation_triggered,
            inflation_risk=inflation_risk,
            recommendation_only=True,
            recommendation_flags=recommendation_flags,
        )
