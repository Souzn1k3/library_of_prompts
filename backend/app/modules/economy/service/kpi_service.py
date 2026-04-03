from __future__ import annotations

import csv
import io
import statistics
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.db.models import EconomyDailyKpi
from app.modules.economy.model.kpis import (
    EconomyDailyKpiRead,
    EconomyKpiAggregateRead,
    EconomyKpiSummaryRead,
)
from app.modules.economy.repository.kpi_repository import EconomyKpiRepository
from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_CONTROL,
    ECONOMY_EXPERIMENT_NAME,
    ECONOMY_EXPERIMENT_TREATMENT,
    economy_experiment_variant,
)


log = get_logger(__name__)
_AGGREGATION_LOCK_KEY = 934_270_019
_DEFAULT_COHORTS = (ECONOMY_EXPERIMENT_CONTROL, ECONOMY_EXPERIMENT_TREATMENT)


def _day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def _day_from_dt(value: datetime) -> date:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).date()
    return value.astimezone(timezone.utc).date()


def _daterange(start_date: date, end_date: date) -> list[date]:
    if end_date < start_date:
        return []
    span = (end_date - start_date).days
    return [start_date + timedelta(days=index) for index in range(span + 1)]


class EconomyKpiService:
    def __init__(self, repo: EconomyKpiRepository) -> None:
        self._repo = repo

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return round(float(numerator) / float(denominator), 4)

    def _mean(self, values: list[float], *, digits: int = 2) -> float | None:
        if not values:
            return None
        return round(float(statistics.fmean(values)), digits)

    def _median(self, values: list[float], *, digits: int = 2) -> float | None:
        if not values:
            return None
        return round(float(statistics.median(values)), digits)

    async def aggregate_recent_days(
        self,
        *,
        lookback_days: int = 35,
        include_today: bool = True,
        experiment_name: str = ECONOMY_EXPERIMENT_NAME,
    ) -> int:
        horizon = max(1, int(lookback_days))
        today = datetime.now(timezone.utc).date()
        end_date = today if include_today else today - timedelta(days=1)
        start_date = end_date - timedelta(days=horizon - 1)
        return await self.aggregate_date_range(
            start_date=start_date,
            end_date=end_date,
            experiment_name=experiment_name,
        )

    async def aggregate_date_range(
        self,
        *,
        start_date: date,
        end_date: date,
        experiment_name: str = ECONOMY_EXPERIMENT_NAME,
    ) -> int:
        if end_date < start_date:
            return 0

        locked = await self._repo.try_acquire_aggregation_lock(lock_key=_AGGREGATION_LOCK_KEY)
        if not locked:
            log.info("economy_kpi_aggregation_skipped_lock_not_acquired")
            return 0

        days = _daterange(start_date, end_date)
        start_at = _day_start(start_date)
        end_at = _day_start(end_date + timedelta(days=1))
        retention_start_at = _day_start(start_date - timedelta(days=7))

        purchases = await self._repo.list_completed_purchases_between(start_at=start_at, end_at=end_at)
        transactions = await self._repo.list_currency_transactions_between(start_at=start_at, end_at=end_at)
        mission_events = await self._repo.list_mission_completion_events_between(
            start_at=start_at,
            end_at=end_at,
        )
        analytics = await self._repo.list_analytics_events_between(start_at=start_at, end_at=end_at)
        created_extended = await self._repo.list_users_created_between(
            start_at=retention_start_at,
            end_at=end_at,
        )

        active_users_by_day: dict[date, set[uuid.UUID]] = defaultdict(set)
        created_users_by_day: dict[date, set[uuid.UUID]] = defaultdict(set)
        store_views_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(lambda: defaultdict(int))
        wallet_views_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(lambda: defaultdict(int))
        mission_completions_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        store_purchases_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        lmn_earned_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(lambda: defaultdict(int))
        lmn_spent_by_day_user: dict[date, dict[uuid.UUID, int]] = defaultdict(lambda: defaultdict(int))
        relevant_users: set[uuid.UUID] = set()

        for user_id, created_at in created_extended:
            day = _day_from_dt(created_at)
            created_users_by_day[day].add(user_id)
            relevant_users.add(user_id)

        for user_id, created_at in purchases:
            day = _day_from_dt(created_at)
            active_users_by_day[day].add(user_id)
            store_purchases_by_day_user[day][user_id] += 1
            relevant_users.add(user_id)

        for user_id, amount, _balance_after, created_at in transactions:
            day = _day_from_dt(created_at)
            active_users_by_day[day].add(user_id)
            if amount >= 0:
                lmn_earned_by_day_user[day][user_id] += int(amount)
            else:
                lmn_spent_by_day_user[day][user_id] += abs(int(amount))
            relevant_users.add(user_id)

        for user_id, created_at in mission_events:
            day = _day_from_dt(created_at)
            active_users_by_day[day].add(user_id)
            relevant_users.add(user_id)

        for user_id, event_name, context_page, _metadata, occurred_at in analytics:
            day = _day_from_dt(occurred_at)
            if user_id is not None:
                active_users_by_day[day].add(user_id)
                relevant_users.add(user_id)
                if event_name == "store_offer_viewed":
                    store_views_by_day_user[day][user_id] += 1
                elif event_name == "mission_completed":
                    mission_completions_by_day_user[day][user_id] += 1
                if event_name == "page_viewed" and "wallet" in context_page.lower():
                    wallet_views_by_day_user[day][user_id] += 1

        if not relevant_users:
            rows: list[dict[str, Any]] = []
            for day in days:
                for cohort in _DEFAULT_COHORTS:
                    rows.append(
                        {
                            "date": day,
                            "experiment_name": experiment_name,
                            "cohort": cohort,
                            "active_users": 0,
                            "new_users": 0,
                            "first_purchase_users": 0,
                            "second_purchase_48h_users": 0,
                            "second_purchase_48h_rate": 0.0,
                            "d1_retention_rate": 0.0,
                            "d7_retention_rate": 0.0,
                            "lmn_earned": 0,
                            "lmn_spent": 0,
                            "lmn_spent_earned_ratio": 0.0,
                            "avg_balance": 0.0,
                            "median_balance": 0.0,
                            "store_views": 0,
                            "store_purchases": 0,
                            "store_conversion_rate": 0.0,
                            "wallet_views": 0,
                            "mission_completions": 0,
                            "avg_time_to_first_purchase_hours": None,
                            "avg_time_to_second_purchase_hours": None,
                        }
                    )
            inserted = await self._repo.upsert_daily_kpis(rows=rows)
            log.info("economy_kpi_aggregation_complete", start_date=start_date.isoformat(), end_date=end_date.isoformat(), rows=inserted)
            return inserted

        user_created_rows = await self._repo.list_users_by_ids(user_ids=relevant_users)
        user_created_at: dict[uuid.UUID, datetime] = {user_id: created_at for user_id, created_at in user_created_rows}

        first_two_purchases = await self._repo.list_first_two_purchases_for_users(
            user_ids=relevant_users,
            end_at=end_at,
        )
        first_purchase_at: dict[uuid.UUID, datetime] = {}
        second_purchase_at: dict[uuid.UUID, datetime] = {}
        for user_id, purchase_rank, created_at in first_two_purchases:
            if purchase_rank == 1:
                first_purchase_at[user_id] = created_at
            elif purchase_rank == 2:
                second_purchase_at[user_id] = created_at

        assignments = await self._repo.list_experiment_assignments_for_users(
            user_ids=relevant_users,
            end_at=end_at,
        )
        assignment_history: dict[uuid.UUID, list[tuple[datetime, str]]] = defaultdict(list)
        for user_id, occurred_at, metadata in assignments:
            meta = metadata or {}
            event_experiment = str(meta.get("experiment_name") or "")
            event_variant = str(meta.get("experiment_variant") or "")
            if event_experiment != experiment_name:
                continue
            if not event_variant:
                continue
            assignment_history[user_id].append((occurred_at, event_variant))

        balance_checkpoints = await self._repo.list_balance_checkpoints_for_users(
            user_ids=relevant_users,
            end_at=end_at,
        )
        checkpoints_by_user: dict[uuid.UUID, list[tuple[datetime, int]]] = defaultdict(list)
        for user_id, created_at, balance_after in balance_checkpoints:
            checkpoints_by_user[user_id].append((created_at, balance_after))
        current_balances = await self._repo.list_current_balances_for_users(user_ids=relevant_users)

        all_days_for_cohorts = _daterange(start_date - timedelta(days=7), end_date)
        cohort_by_user_day: dict[tuple[uuid.UUID, date], str] = {}
        for user_id in relevant_users:
            history = assignment_history.get(user_id, [])
            history_index = 0
            latest_variant: str | None = None
            for day in all_days_for_cohorts:
                day_end = _day_start(day + timedelta(days=1))
                while history_index < len(history) and history[history_index][0] < day_end:
                    latest_variant = history[history_index][1]
                    history_index += 1
                if latest_variant:
                    cohort_by_user_day[(user_id, day)] = latest_variant
                    continue
                first_purchase = first_purchase_at.get(user_id)
                payer_status = "payer" if first_purchase is not None and first_purchase < day_end else "non_payer"
                cohort_by_user_day[(user_id, day)] = economy_experiment_variant(
                    user_id=user_id,
                    payer_status=payer_status,
                )

        balance_by_user_day: dict[tuple[uuid.UUID, date], int] = {}
        for user_id in relevant_users:
            checkpoints = checkpoints_by_user.get(user_id, [])
            idx = 0
            last_balance: int | None = None
            for day in days:
                day_end = _day_start(day + timedelta(days=1))
                while idx < len(checkpoints) and checkpoints[idx][0] < day_end:
                    last_balance = checkpoints[idx][1]
                    idx += 1
                if last_balance is not None:
                    balance_by_user_day[(user_id, day)] = last_balance

        rows: list[dict[str, Any]] = []
        for day in days:
            cohorts = set(_DEFAULT_COHORTS)
            day_active_users = active_users_by_day.get(day, set())
            day_new_users = created_users_by_day.get(day, set())

            first_purchase_users = {
                user_id
                for user_id, created_at in first_purchase_at.items()
                if _day_from_dt(created_at) == day
            }
            second_purchase_48h_users = {
                user_id
                for user_id, second_at in second_purchase_at.items()
                if _day_from_dt(second_at) == day
                and user_id in first_purchase_at
                and (second_at - first_purchase_at[user_id]) <= timedelta(hours=48)
            }

            for user_id in day_active_users | day_new_users | first_purchase_users | second_purchase_48h_users:
                cohorts.add(cohort_by_user_day.get((user_id, day), ECONOMY_EXPERIMENT_CONTROL))

            for cohort in sorted(cohorts):
                active_users = [uid for uid in day_active_users if cohort_by_user_day.get((uid, day)) == cohort]
                new_users = [uid for uid in day_new_users if cohort_by_user_day.get((uid, day)) == cohort]
                first_users = [uid for uid in first_purchase_users if cohort_by_user_day.get((uid, day)) == cohort]
                second_48h_users = [
                    uid for uid in second_purchase_48h_users if cohort_by_user_day.get((uid, day)) == cohort
                ]

                d1_source_day = day - timedelta(days=1)
                d1_cohort_users = [
                    uid
                    for uid in created_users_by_day.get(d1_source_day, set())
                    if cohort_by_user_day.get((uid, d1_source_day)) == cohort
                ]
                d1_retained = len([uid for uid in d1_cohort_users if uid in day_active_users])

                d7_source_day = day - timedelta(days=7)
                d7_cohort_users = [
                    uid
                    for uid in created_users_by_day.get(d7_source_day, set())
                    if cohort_by_user_day.get((uid, d7_source_day)) == cohort
                ]
                d7_retained = len([uid for uid in d7_cohort_users if uid in day_active_users])

                lmn_earned = sum(
                    lmn_earned_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )
                lmn_spent = sum(
                    lmn_spent_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )

                balances: list[float] = []
                for uid in active_users:
                    balance = balance_by_user_day.get((uid, day))
                    if balance is None:
                        balance = current_balances.get(uid)
                    if balance is not None:
                        balances.append(float(balance))

                store_views = sum(
                    store_views_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )
                store_purchases = sum(
                    store_purchases_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )
                wallet_views = sum(
                    wallet_views_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )
                mission_completions = sum(
                    mission_completions_by_day_user.get(day, {}).get(uid, 0)
                    for uid in active_users
                )

                first_purchase_hours: list[float] = []
                for uid in first_users:
                    created_at = user_created_at.get(uid)
                    first_at = first_purchase_at.get(uid)
                    if created_at is None or first_at is None:
                        continue
                    first_purchase_hours.append(max(0.0, (first_at - created_at).total_seconds() / 3600.0))

                second_purchase_hours: list[float] = []
                for uid in second_48h_users:
                    first_at = first_purchase_at.get(uid)
                    second_at = second_purchase_at.get(uid)
                    if first_at is None or second_at is None:
                        continue
                    second_purchase_hours.append(max(0.0, (second_at - first_at).total_seconds() / 3600.0))

                rows.append(
                    {
                        "date": day,
                        "experiment_name": experiment_name,
                        "cohort": cohort,
                        "active_users": len(active_users),
                        "new_users": len(new_users),
                        "first_purchase_users": len(first_users),
                        "second_purchase_48h_users": len(second_48h_users),
                        "second_purchase_48h_rate": self._ratio(len(second_48h_users), len(first_users)),
                        "d1_retention_rate": self._ratio(d1_retained, len(d1_cohort_users)),
                        "d7_retention_rate": self._ratio(d7_retained, len(d7_cohort_users)),
                        "lmn_earned": int(lmn_earned),
                        "lmn_spent": int(lmn_spent),
                        "lmn_spent_earned_ratio": self._ratio(int(lmn_spent), int(lmn_earned)),
                        "avg_balance": round(self._mean(balances, digits=2) or 0.0, 2),
                        "median_balance": round(self._median(balances, digits=2) or 0.0, 2),
                        "store_views": int(store_views),
                        "store_purchases": int(store_purchases),
                        "store_conversion_rate": self._ratio(int(store_purchases), int(store_views)),
                        "wallet_views": int(wallet_views),
                        "mission_completions": int(mission_completions),
                        "avg_time_to_first_purchase_hours": self._mean(first_purchase_hours, digits=2),
                        "avg_time_to_second_purchase_hours": self._mean(second_purchase_hours, digits=2),
                    }
                )

        inserted = await self._repo.upsert_daily_kpis(rows=rows)
        log.info(
            "economy_kpi_aggregation_complete",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            rows=len(rows),
            affected=inserted,
        )
        return inserted

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
        for cohort in _DEFAULT_COHORTS:
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
