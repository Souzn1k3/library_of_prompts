from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EconomyArmKpiRead(BaseModel):
    variant: str
    users: int
    repeat_purchase_rate: float
    spend_frequency: float
    median_time_to_second_purchase_hours: float | None = None
    d1_retention: float
    d7_retention: float
    d14_retention: float
    lmn_circulation_ratio: float
    offer_conversion: float
    streak_survival: float
    goal_completion_rate: float


class EconomyGuardrailRead(BaseModel):
    retention_drop_flag: bool
    inflation_breach_flag: bool
    mission_completion_collapse_flag: bool


class EconomyExperimentKpiRead(BaseModel):
    experiment_name: str
    generated_at: datetime
    window_days: int
    arms: list[EconomyArmKpiRead] = Field(default_factory=list)
    guardrails: EconomyGuardrailRead
    minimum_runtime_days: int = 14
    is_decision_ready: bool
    recommended_next_step: str


class EconomyTuningRead(BaseModel):
    computed_at: datetime
    window_days: int
    circulation_ratio_7d: float
    median_idle_balance: float
    inflation_triggered: bool
    inflation_risk: str
    recommendation_only: bool = True
    recommendation_flags: list[str] = Field(default_factory=list)
