from __future__ import annotations

from datetime import datetime, date

from pydantic import BaseModel, Field


class GrowthMetricSnapshotRead(BaseModel):
    window_days: int
    computed_at: datetime
    activation_rate: float
    d1_retention: float
    d7_retention: float
    free_to_paid_conversion: float
    upgrade_intent_rate: float
    ltv_proxy_usd: float


class GrowthFunnelStepRead(BaseModel):
    key: str
    label: str
    users: int
    conversion_from_prev: float


class GrowthFunnelRead(BaseModel):
    window_days: int
    steps: list[GrowthFunnelStepRead] = Field(default_factory=list)


class GrowthCohortRead(BaseModel):
    cohort_week_start: date
    users: int
    d1_retention: float
    d7_retention: float | None = None
    paid_30d_conversion: float | None = None


class GrowthExperimentVariantRead(BaseModel):
    variant: str
    users: int
    conversion: float
    retention_d7: float


class GrowthExperimentRead(BaseModel):
    key: str
    rollout_percent: int
    variants: list[GrowthExperimentVariantRead] = Field(default_factory=list)


class GrowthFlagRead(BaseModel):
    key: str
    enabled: bool
    rollout_percent: int
    target: str
    reason: str


class GrowthExperimentAssignmentRead(BaseModel):
    key: str
    variant: str
    rollout_percent: int
    eligible: bool
    reason: str


class GrowthRuntimeRead(BaseModel):
    computed_at: datetime
    session_id: str
    flags: list[GrowthFlagRead] = Field(default_factory=list)
    experiments: list[GrowthExperimentAssignmentRead] = Field(default_factory=list)


class GrowthDashboardRead(BaseModel):
    metrics: GrowthMetricSnapshotRead
    funnel: GrowthFunnelRead
    cohorts: list[GrowthCohortRead] = Field(default_factory=list)
    experiments: list[GrowthExperimentRead] = Field(default_factory=list)
    rollout_flags: list[GrowthFlagRead] = Field(default_factory=list)

