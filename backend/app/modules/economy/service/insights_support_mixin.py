from __future__ import annotations

import statistics
import uuid
from datetime import date, datetime, timedelta

from app.modules.economy.model.insights import EconomyArmKpiRead
from app.modules.economy.service.insights_constants import SINK_REASONS, SOURCE_REASONS


class EconomyInsightsSupportMixin:
    def _round(self, value: float | None) -> float | None:
        if value is None:
            return None
        return round(float(value), 4)

    def _retention_ratio(
        self,
        *,
        first_activity: dict[uuid.UUID, date],
        activity_days: dict[uuid.UUID, set[date]],
        offset_days: int,
        end_date: date,
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
        activity_days: dict[uuid.UUID, set[date]],
        first_activity: dict[uuid.UUID, date],
        tx_by_user: dict[uuid.UUID, list[tuple[int, str]]],
        offer_views_by_user: dict[uuid.UUID, int],
        offer_conversions_by_user: dict[uuid.UUID, int],
        goals_completed_users: set[uuid.UUID],
        wallet_rows: dict[uuid.UUID, tuple[int, int, int, int]],
        end_date: date,
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
