from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.db.models import BillingProvider, PlanTier, SubscriptionStatus


class PlanPublicRead(BaseModel):
    tier: PlanTier
    name: str
    description: str | None
    price_usd_month: int
    features: list[str]
    sort_order: int
    is_active: bool


class CheckoutSessionRequest(BaseModel):
    tier: PlanTier
    success_url: str | None = Field(default=None, max_length=1000)
    cancel_url: str | None = Field(default=None, max_length=1000)

    @field_validator("success_url", "cancel_url")
    @classmethod
    def normalize_urls(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str | None = None


class BillingPortalRequest(BaseModel):
    return_url: str | None = Field(default=None, max_length=1000)

    @field_validator("return_url")
    @classmethod
    def normalize_url(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class BillingPortalResponse(BaseModel):
    url: str


class BillingStatusRead(BaseModel):
    plan_tier: PlanTier
    subscription_tier: PlanTier | None
    provider: BillingProvider | None
    status: SubscriptionStatus | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    updated_at: datetime | None
