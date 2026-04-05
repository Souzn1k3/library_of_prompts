from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from app.modules.economy.service.experiment_service import (
    ECONOMY_EXPERIMENT_CONTROL,
    ECONOMY_EXPERIMENT_TREATMENT,
)


AGGREGATION_LOCK_KEY = 934_270_019
DEFAULT_COHORTS = (ECONOMY_EXPERIMENT_CONTROL, ECONOMY_EXPERIMENT_TREATMENT)


def day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def day_from_dt(value: datetime) -> date:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).date()
    return value.astimezone(timezone.utc).date()


def daterange(start_date: date, end_date: date) -> list[date]:
    if end_date < start_date:
        return []
    span = (end_date - start_date).days
    return [start_date + timedelta(days=index) for index in range(span + 1)]
