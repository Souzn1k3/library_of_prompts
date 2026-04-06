from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChannelSpendUpsertWrite(BaseModel):
    spend_day: date
    source: str = Field(min_length=1, max_length=120)
    medium: str | None = Field(default=None, max_length=120)
    campaign: str | None = Field(default=None, max_length=160)
    ad_id: str | None = Field(default=None, max_length=120)
    creative_id: str | None = Field(default=None, max_length=120)
    cost_usd: float = Field(ge=0.0, le=1_000_000.0)
    clicks: int = Field(default=0, ge=0, le=100_000_000)
    impressions: int = Field(default=0, ge=0, le=1_000_000_000)
    dedupe_key: str | None = Field(default=None, min_length=4, max_length=220)


class ChannelSpendUpsertRead(BaseModel):
    id: str
    spend_day: date
    source: str
    medium: str | None
    campaign: str | None
    ad_id: str | None
    creative_id: str | None
    cost_usd: float
    clicks: int
    impressions: int
    dedupe_key: str
    updated_at: datetime


class GtmHeadlineRead(BaseModel):
    window_days: int
    computed_at: datetime
    traffic_sessions: int
    signups: int
    activated_users: int
    paid_users: int
    revenue_usd: float
    spend_usd: float
    blended_cac_usd: float | None
    blended_roi_percent: float | None


class GtmChannelPerformanceRead(BaseModel):
    source: str
    campaign: str | None
    traffic_sessions: int
    ad_clicks: int
    landing_views: int
    signups: int
    activated_users: int
    paid_users: int
    revenue_usd: float
    spend_usd: float
    signup_rate: float
    activation_rate: float
    conversion_rate: float
    cac_usd: float | None
    roi_percent: float | None
    ltv_cac_proxy: float | None


class GtmSourceFunnelRead(BaseModel):
    source: str
    acquired: int
    signed_up: int
    activated: int
    paid: int
    acquired_to_signup: float
    signup_to_activated: float
    activated_to_paid: float


class GtmCreativePerformanceRead(BaseModel):
    source: str
    campaign: str | None
    ad_id: str | None
    creative_id: str | None
    clicks: int
    signups: int
    activated_users: int
    paid_users: int
    revenue_usd: float
    conversion_rate: float


class GtmScaleSignalRead(BaseModel):
    signal: Literal["scale_channel", "kill_channel"]
    source: str
    campaign: str | None
    reason: str
    roi_percent: float | None
    cac_usd: float | None
    conversion_rate: float


class GtmDashboardRead(BaseModel):
    headline: GtmHeadlineRead
    channels: list[GtmChannelPerformanceRead] = Field(default_factory=list)
    funnel_by_source: list[GtmSourceFunnelRead] = Field(default_factory=list)
    top_campaigns: list[GtmChannelPerformanceRead] = Field(default_factory=list)
    top_creatives: list[GtmCreativePerformanceRead] = Field(default_factory=list)
    signals: list[GtmScaleSignalRead] = Field(default_factory=list)

