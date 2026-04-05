from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone

from app.modules.economy.model.insights import EconomyTuningRead
from app.modules.economy.service.insights_constants import SINK_REASONS, SOURCE_REASONS


class EconomyInsightsTuningMixin:
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
