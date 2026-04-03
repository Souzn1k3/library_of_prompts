from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class EconomyDailyKpiRead(BaseModel):
    date: date
    experiment_name: str
    cohort: str
    active_users: int
    new_users: int
    first_purchase_users: int
    second_purchase_48h_users: int
    second_purchase_48h_rate: float
    d1_retention_rate: float
    d7_retention_rate: float
    lmn_earned: int
    lmn_spent: int
    lmn_spent_earned_ratio: float
    avg_balance: float
    median_balance: float
    store_views: int
    store_purchases: int
    store_conversion_rate: float
    wallet_views: int
    mission_completions: int
    avg_time_to_first_purchase_hours: float | None = None
    avg_time_to_second_purchase_hours: float | None = None

    model_config = {"from_attributes": True}


class EconomyKpiAggregateRead(BaseModel):
    period_start: date
    period_end: date
    experiment_name: str
    cohort: str
    days: int
    active_users: int
    new_users: int
    first_purchase_users: int
    second_purchase_48h_users: int
    second_purchase_48h_rate: float
    d1_retention_rate: float
    d7_retention_rate: float
    lmn_earned: int
    lmn_spent: int
    lmn_spent_earned_ratio: float
    avg_balance: float
    median_balance: float
    store_views: int
    store_purchases: int
    store_conversion_rate: float
    wallet_views: int
    mission_completions: int
    avg_time_to_first_purchase_hours: float | None = None
    avg_time_to_second_purchase_hours: float | None = None


class EconomyKpiSummaryRead(BaseModel):
    generated_at: datetime
    experiment_name: str
    today: list[EconomyDailyKpiRead] = Field(default_factory=list)
    yesterday: list[EconomyDailyKpiRead] = Field(default_factory=list)
    last_7_days: list[EconomyKpiAggregateRead] = Field(default_factory=list)
    week_to_date: list[EconomyKpiAggregateRead] = Field(default_factory=list)
    month_to_date: list[EconomyKpiAggregateRead] = Field(default_factory=list)
    control_vs_variant: list[EconomyKpiAggregateRead] = Field(default_factory=list)
