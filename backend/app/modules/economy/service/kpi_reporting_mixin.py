from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.infrastructure.db.models import EconomyDailyKpi
from app.modules.economy.model.kpis import EconomyDailyKpiRead, EconomyKpiAggregateRead, EconomyKpiSummaryRead
from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_CONTROL,
    ECONOMY_EXPERIMENT_NAME,
    ECONOMY_EXPERIMENT_TREATMENT,
)
from app.modules.economy.service.kpi_shared import DEFAULT_COHORTS


class EconomyKpiReportingMixin:
    def _aggregate_rows(
        self,
        *,
        rows: list[EconomyDailyKpi],
        period_start: date,
        period_end: date,
        experiment_name: str,
    ) -> list[EconomyKpiAggregateRead]:
        grouped: dict[str, list[EconomyDailyKpi]] = defaultdict(list)
        for row in rows:
            grouped[row.cohort].append(row)

        aggregates: list[EconomyKpiAggregateRead] = []
        for cohort, cohort_rows in grouped.items():
            days = len(cohort_rows)
            active_users = sum(int(row.active_users) for row in cohort_rows)
            new_users = sum(int(row.new_users) for row in cohort_rows)
            first_purchase_users = sum(int(row.first_purchase_users) for row in cohort_rows)
            second_purchase_48h_users = sum(int(row.second_purchase_48h_users) for row in cohort_rows)
            lmn_earned = sum(int(row.lmn_earned) for row in cohort_rows)
            lmn_spent = sum(int(row.lmn_spent) for row in cohort_rows)
            store_views = sum(int(row.store_views) for row in cohort_rows)
            store_purchases = sum(int(row.store_purchases) for row in cohort_rows)
            wallet_views = sum(int(row.wallet_views) for row in cohort_rows)
            mission_completions = sum(int(row.mission_completions) for row in cohort_rows)

            avg_balances = [float(row.avg_balance) for row in cohort_rows]
            median_balances = [float(row.median_balance) for row in cohort_rows]
            d1_rates = [float(row.d1_retention_rate) for row in cohort_rows]
            d7_rates = [float(row.d7_retention_rate) for row in cohort_rows]
            first_purchase_times = [
                float(row.avg_time_to_first_purchase_hours)
                for row in cohort_rows
                if row.avg_time_to_first_purchase_hours is not None
            ]
            second_purchase_times = [
                float(row.avg_time_to_second_purchase_hours)
                for row in cohort_rows
                if row.avg_time_to_second_purchase_hours is not None
            ]

            aggregates.append(
                EconomyKpiAggregateRead(
                    period_start=period_start,
                    period_end=period_end,
                    experiment_name=experiment_name,
                    cohort=cohort,
                    days=days,
                    active_users=active_users,
                    new_users=new_users,
                    first_purchase_users=first_purchase_users,
                    second_purchase_48h_users=second_purchase_48h_users,
                    second_purchase_48h_rate=self._ratio(second_purchase_48h_users, first_purchase_users),
                    d1_retention_rate=round(self._mean(d1_rates, digits=4) or 0.0, 4),
                    d7_retention_rate=round(self._mean(d7_rates, digits=4) or 0.0, 4),
                    lmn_earned=lmn_earned,
                    lmn_spent=lmn_spent,
                    lmn_spent_earned_ratio=self._ratio(lmn_spent, lmn_earned),
                    avg_balance=round(self._mean(avg_balances, digits=2) or 0.0, 2),
                    median_balance=round(self._mean(median_balances, digits=2) or 0.0, 2),
                    store_views=store_views,
                    store_purchases=store_purchases,
                    store_conversion_rate=self._ratio(store_purchases, store_views),
                    wallet_views=wallet_views,
                    mission_completions=mission_completions,
                    avg_time_to_first_purchase_hours=self._mean(first_purchase_times, digits=2),
                    avg_time_to_second_purchase_hours=self._mean(second_purchase_times, digits=2),
                )
            )

        existing = {item.cohort for item in aggregates}
        for cohort in DEFAULT_COHORTS:
            if cohort in existing:
                continue
            aggregates.append(
                EconomyKpiAggregateRead(
                    period_start=period_start,
                    period_end=period_end,
                    experiment_name=experiment_name,
                    cohort=cohort,
                    days=0,
                    active_users=0,
                    new_users=0,
                    first_purchase_users=0,
                    second_purchase_48h_users=0,
                    second_purchase_48h_rate=0.0,
                    d1_retention_rate=0.0,
                    d7_retention_rate=0.0,
                    lmn_earned=0,
                    lmn_spent=0,
                    lmn_spent_earned_ratio=0.0,
                    avg_balance=0.0,
                    median_balance=0.0,
                    store_views=0,
                    store_purchases=0,
                    store_conversion_rate=0.0,
                    wallet_views=0,
                    mission_completions=0,
                    avg_time_to_first_purchase_hours=None,
                    avg_time_to_second_purchase_hours=None,
                )
            )
        return sorted(aggregates, key=lambda row: row.cohort)

    async def summary(self, *, experiment_name: str = ECONOMY_EXPERIMENT_NAME) -> EconomyKpiSummaryRead:
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        last_7_start = today - timedelta(days=6)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        summary_start = min(last_7_start, week_start, month_start, yesterday)

        rows = await self._repo.list_kpis(
            start_date=summary_start,
            end_date=today,
            experiment_name=experiment_name,
        )

        today_rows = [EconomyDailyKpiRead.model_validate(row) for row in rows if row.date == today]
        yesterday_rows = [EconomyDailyKpiRead.model_validate(row) for row in rows if row.date == yesterday]
        last_7_rows = [row for row in rows if last_7_start <= row.date <= today]
        week_rows = [row for row in rows if week_start <= row.date <= today]
        month_rows = [row for row in rows if month_start <= row.date <= today]

        last_7_aggregates = self._aggregate_rows(
            rows=last_7_rows,
            period_start=last_7_start,
            period_end=today,
            experiment_name=experiment_name,
        )
        week_aggregates = self._aggregate_rows(
            rows=week_rows,
            period_start=week_start,
            period_end=today,
            experiment_name=experiment_name,
        )
        month_aggregates = self._aggregate_rows(
            rows=month_rows,
            period_start=month_start,
            period_end=today,
            experiment_name=experiment_name,
        )
        control_vs_variant = [
            row
            for row in last_7_aggregates
            if row.cohort in {ECONOMY_EXPERIMENT_CONTROL, ECONOMY_EXPERIMENT_TREATMENT}
        ]

        return EconomyKpiSummaryRead(
            generated_at=datetime.now(timezone.utc),
            experiment_name=experiment_name,
            today=today_rows,
            yesterday=yesterday_rows,
            last_7_days=last_7_aggregates,
            week_to_date=week_aggregates,
            month_to_date=month_aggregates,
            control_vs_variant=control_vs_variant,
        )

    async def export_csv(
        self,
        *,
        experiment_name: str = ECONOMY_EXPERIMENT_NAME,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[str, bytes]:
        today = datetime.now(timezone.utc).date()
        range_end = end_date or today
        range_start = start_date or (range_end - timedelta(days=90))
        if range_end < range_start:
            range_start, range_end = range_end, range_start

        rows = await self._repo.list_kpis(
            start_date=range_start,
            end_date=range_end,
            experiment_name=experiment_name,
        )

        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, lineterminator="\r\n")
        header = [
            "date",
            "experiment_name",
            "cohort",
            "active_users",
            "new_users",
            "first_purchase_users",
            "second_purchase_48h_users",
            "second_purchase_48h_rate",
            "d1_retention_rate",
            "d7_retention_rate",
            "lmn_earned",
            "lmn_spent",
            "lmn_spent_earned_ratio",
            "avg_balance",
            "median_balance",
            "store_views",
            "store_purchases",
            "store_conversion_rate",
            "wallet_views",
            "mission_completions",
            "avg_time_to_first_purchase_hours",
            "avg_time_to_second_purchase_hours",
        ]
        writer.writerow(header)

        for row in rows:
            writer.writerow(
                [
                    row.date.isoformat(),
                    row.experiment_name,
                    row.cohort,
                    int(row.active_users),
                    int(row.new_users),
                    int(row.first_purchase_users),
                    int(row.second_purchase_48h_users),
                    float(row.second_purchase_48h_rate),
                    float(row.d1_retention_rate),
                    float(row.d7_retention_rate),
                    int(row.lmn_earned),
                    int(row.lmn_spent),
                    float(row.lmn_spent_earned_ratio),
                    float(row.avg_balance),
                    float(row.median_balance),
                    int(row.store_views),
                    int(row.store_purchases),
                    float(row.store_conversion_rate),
                    int(row.wallet_views),
                    int(row.mission_completions),
                    (
                        ""
                        if row.avg_time_to_first_purchase_hours is None
                        else float(row.avg_time_to_first_purchase_hours)
                    ),
                    (
                        ""
                        if row.avg_time_to_second_purchase_hours is None
                        else float(row.avg_time_to_second_purchase_hours)
                    ),
                ]
            )

        csv_body = buffer.getvalue()
        content = ("\ufeffsep=,\r\n" + csv_body).encode("utf-8")
        filename = f"economy_kpis_{range_start.isoformat()}_{range_end.isoformat()}.csv"
        return filename, content
