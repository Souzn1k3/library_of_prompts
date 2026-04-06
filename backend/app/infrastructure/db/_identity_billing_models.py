from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._catalog_models import Prompt
from ._enums import (
    BillingProvider,
    ContributorTier,
    OnboardingGoal,
    OnboardingRole,
    PlanTier,
    SubscriptionStatus,
)
from ._user_model import User
from .base import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    event_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="web", index=True)
    context_page: Mapped[str] = mapped_column(String(260), nullable=False, index=True)
    context_feature: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(160), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User | None"] = relationship(back_populates="analytics_events")


class SessionAttribution(Base):
    __tablename__ = "session_attributions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    linked_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    first_utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    first_ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    last_ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    linked_user: Mapped["User | None"] = relationship(back_populates="session_attributions")


class UserAttribution(Base):
    __tablename__ = "user_attributions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    first_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    first_utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    first_ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    first_referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_utm_campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    last_ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    last_referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="user_attribution")


class AuthRefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class ChannelSpendEntry(Base):
    __tablename__ = "channel_spend_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spend_day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    campaign: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    ad_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    creative_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    cost_usd_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dedupe_key: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False, length=32),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price_usd_month: Mapped[int] = mapped_column(Integer, nullable=False)
    price_rub_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_paid_prompt_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_purchase_discount_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lumen_purchase_discount_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stripe_price_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    provider: Mapped[BillingProvider] = mapped_column(
        Enum(BillingProvider, native_enum=False, length=16),
        nullable=False,
        default=BillingProvider.stripe,
    )
    provider_customer_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="billing_customer")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider: Mapped[BillingProvider] = mapped_column(
        Enum(BillingProvider, native_enum=False, length=16),
        nullable=False,
        default=BillingProvider.stripe,
    )
    provider_subscription_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")
    events: Mapped[list["SubscriptionEvent"]] = relationship(back_populates="subscription")


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provider: Mapped[BillingProvider] = mapped_column(
        Enum(BillingProvider, native_enum=False, length=16),
        nullable=False,
    )
    provider_event_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_event_id",
            "subscription_id",
            name="uq_subscription_event_provider_event_subscription",
        ),
    )

    subscription: Mapped["Subscription | None"] = relationship(back_populates="events")
    user: Mapped["User | None"] = relationship(back_populates="subscription_events")


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[BillingProvider] = mapped_column(
        Enum(BillingProvider, native_enum=False, length=16),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_processed_webhook_events_provider_event"),
    )


class OnboardingProfile(Base):
    __tablename__ = "onboarding_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    role: Mapped[OnboardingRole | None] = mapped_column(
        Enum(OnboardingRole, native_enum=False, length=32),
        nullable=True,
    )
    goal: Mapped[OnboardingGoal | None] = mapped_column(
        Enum(OnboardingGoal, native_enum=False, length=32),
        nullable=True,
    )
    ai_context: Mapped[str | None] = mapped_column(String(120), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_win_prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_win_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="onboarding_profile")
    first_win_prompt: Mapped["Prompt | None"] = relationship()


class OnboardingEvent(Base):
    __tablename__ = "onboarding_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="onboarding_events")


class ContributorProfile(Base):
    __tablename__ = "contributor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reputation_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    reputation_tier: Mapped[ContributorTier] = mapped_column(
        Enum(ContributorTier, native_enum=False, length=24),
        nullable=False,
        default=ContributorTier.new,
        index=True,
    )
    total_submissions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_submissions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_submissions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejection_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_saves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mission_success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_prompt_quality: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="contributor_profile")


