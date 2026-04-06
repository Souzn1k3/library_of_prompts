from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class RevenueHeadlineRead(BaseModel):
    window_days: int
    computed_at: datetime
    mrr_usd: float
    arr_usd: float
    arpu_usd: float
    free_to_paid_conversion: float
    revenue_per_user_usd: float
    ltv_proxy_usd: float
    churn_rate: float
    paying_user_retention_d30: float


class RevenueFunnelStepRead(BaseModel):
    key: str
    label: str
    users: int
    conversion_from_prev: float
    dropoff_from_prev: float


class RevenueFunnelRead(BaseModel):
    steps: list[RevenueFunnelStepRead] = Field(default_factory=list)


class RevenueSourceRead(BaseModel):
    source: str
    acquired_users: int
    paid_users: int
    conversion_rate: float
    mrr_usd: float
    arr_usd: float


class RevenueCohortRead(BaseModel):
    cohort_week_start: date
    source: str
    plan_tier: str
    users: int
    paid_users: int
    revenue_usd: float
    retention_d30: float | None = None
    conversion_lag_days: float | None = None


class RevenueExperimentVariantRead(BaseModel):
    experiment_key: str
    variant: str
    views: int
    interactions: int
    upgrades: int
    paid_users: int
    conversion_rate: float
    revenue_per_user_usd: float
    retention_d30: float


class RevenueChurnSignalRead(BaseModel):
    churn_risk_users: int
    canceled_users: int
    inactive_paying_users: int
    generated_at: datetime


class RevenueDashboardRead(BaseModel):
    headline: RevenueHeadlineRead
    funnel: RevenueFunnelRead
    funnel_by_source: list[RevenueSourceRead] = Field(default_factory=list)
    revenue_by_source: list[RevenueSourceRead] = Field(default_factory=list)
    paywall_performance: list[RevenueExperimentVariantRead] = Field(default_factory=list)
    cohorts: list[RevenueCohortRead] = Field(default_factory=list)
    churn_signals: RevenueChurnSignalRead

