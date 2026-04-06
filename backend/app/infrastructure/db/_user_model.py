from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._enums import PlanTier, UserRole
from .base import Base

if TYPE_CHECKING:
    from ._catalog_models import Prompt, SavedPrompt
    from ._economy_models import CurrencyTransaction, UserActiveBoost, UserCurrencyBalance, UserLockedReward, UserPurchase
    from ._identity_billing_models import (
        AnalyticsEvent,
        AuthRefreshToken,
        BillingCustomer,
        ContributorProfile,
        OnboardingEvent,
        OnboardingProfile,
        Subscription,
        SubscriptionEvent,
    )
    from ._marketplace_models import (
        MarketplacePayout,
        MarketplaceTransaction,
        PlanUsageWindow,
        PromptEntitlement,
        PromptPurchase,
        PromptReview,
        PromptReviewReport,
    )
    from ._mission_models import MissionCompletionEvent, UserMissionProgress, UserMissionRewardGrant
    from ._scenario_models import TelegramRewardClaim, UserScenarioWorkspace


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.user)
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False, length=32),
        nullable=False,
        default=PlanTier.free,
    )
    mission_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    premium_unlock_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    telegram_is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    telegram_joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    telegram_last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prompts: Mapped[list["Prompt"]] = relationship(back_populates="author", foreign_keys="Prompt.author_id")
    saved_prompt_links: Mapped[list["SavedPrompt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    billing_customer: Mapped["BillingCustomer | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    subscription_events: Mapped[list["SubscriptionEvent"]] = relationship(back_populates="user")
    onboarding_profile: Mapped["OnboardingProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    onboarding_events: Mapped[list["OnboardingEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mission_progress: Mapped[list["UserMissionProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mission_completion_events: Mapped[list["MissionCompletionEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    mission_reward_grants: Mapped[list["UserMissionRewardGrant"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    currency_balance: Mapped["UserCurrencyBalance | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    currency_transactions: Mapped[list["CurrencyTransaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    purchases: Mapped[list["UserPurchase"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    locked_rewards: Mapped[list["UserLockedReward"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    active_boosts: Mapped[list["UserActiveBoost"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    marketplace_entitlements: Mapped[list["PromptEntitlement"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    marketplace_purchases: Mapped[list["PromptPurchase"]] = relationship(
        back_populates="buyer",
        cascade="all, delete-orphan",
        foreign_keys="PromptPurchase.user_id",
    )
    marketplace_sales: Mapped[list["PromptPurchase"]] = relationship(
        back_populates="seller",
        foreign_keys="PromptPurchase.seller_user_id",
    )
    marketplace_reviews_written: Mapped[list["PromptReview"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        foreign_keys="PromptReview.author_user_id",
    )
    marketplace_reviews_received: Mapped[list["PromptReview"]] = relationship(
        back_populates="seller",
        foreign_keys="PromptReview.seller_user_id",
    )
    marketplace_transactions: Mapped[list["MarketplaceTransaction"]] = relationship(
        back_populates="actor_user",
        cascade="all, delete-orphan",
    )
    marketplace_payouts: Mapped[list["MarketplacePayout"]] = relationship(
        back_populates="seller",
        cascade="all, delete-orphan",
    )
    marketplace_review_reports: Mapped[list["PromptReviewReport"]] = relationship(
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    plan_usage_windows: Mapped[list["PlanUsageWindow"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    contributor_profile: Mapped["ContributorProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    refresh_tokens: Mapped[list["AuthRefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    scenario_workspace_entries: Mapped[list["UserScenarioWorkspace"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    telegram_reward_claims: Mapped[list["TelegramRewardClaim"]] = relationship(
        back_populates="user",
    )
