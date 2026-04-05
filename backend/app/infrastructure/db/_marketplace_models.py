from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._catalog_models import Prompt
from ._enums import (
    MarketplacePayoutStatus,
    MarketplaceSettlementStatus,
    MarketplaceTransactionKind,
    PlanTier,
    PromptAccessSource,
    PromptPaymentMethod,
    PurchaseStatus,
    ReviewModerationStatus,
)
from ._user_model import User
from .base import Base


class PromptPrice(Base):
    __tablename__ = "prompt_prices"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    price_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    price_lumens: Mapped[int] = mapped_column(Integer, nullable=False)
    commission_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
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

    prompt: Mapped["Prompt"] = relationship(back_populates="pricing")


class PlanUsageWindow(Base):
    __tablename__ = "plan_usage_windows"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    included_paid_prompt_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_paid_prompt_unlocks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "plan_tier",
            "window_started_at",
            "window_ends_at",
            name="uq_plan_usage_windows_scope",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="plan_usage_windows")


class PromptPurchase(Base):
    __tablename__ = "prompt_purchases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payment_method: Mapped[PromptPaymentMethod] = mapped_column(
        Enum(PromptPaymentMethod, native_enum=False, length=32),
        nullable=False,
        default=PromptPaymentMethod.lumens,
        index=True,
    )
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus, native_enum=False, length=32),
        nullable=False,
        default=PurchaseStatus.pending,
        index=True,
    )
    settlement_status: Mapped[MarketplaceSettlementStatus] = mapped_column(
        Enum(MarketplaceSettlementStatus, native_enum=False, length=32),
        nullable=False,
        default=MarketplaceSettlementStatus.pending,
        index=True,
    )
    price_rub: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price_lumens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform_fee_rub: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seller_amount_rub: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform_fee_lumens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seller_amount_lumens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    settlement_available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disputed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payout_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("marketplace_payouts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provider_checkout_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    client_token: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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

    buyer: Mapped["User"] = relationship(
        back_populates="marketplace_purchases",
        foreign_keys=[user_id],
    )
    seller: Mapped["User | None"] = relationship(
        back_populates="marketplace_sales",
        foreign_keys=[seller_user_id],
    )
    prompt: Mapped["Prompt"] = relationship(back_populates="marketplace_purchases")
    entitlement: Mapped["PromptEntitlement | None"] = relationship(
        back_populates="purchase",
        uselist=False,
    )
    payout: Mapped["MarketplacePayout | None"] = relationship(back_populates="purchases")
    review: Mapped["PromptReview | None"] = relationship(
        back_populates="purchase",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ledger_entries: Mapped[list["MarketplaceTransaction"]] = relationship(
        back_populates="purchase",
        cascade="all, delete-orphan",
    )


class PromptEntitlement(Base):
    __tablename__ = "prompt_entitlements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_purchases.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    source: Mapped[PromptAccessSource] = mapped_column(
        Enum(PromptAccessSource, native_enum=False, length=32),
        nullable=False,
        default=PromptAccessSource.direct_lumens,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "prompt_id", name="uq_prompt_entitlements_user_prompt"),
    )

    user: Mapped["User"] = relationship(back_populates="marketplace_entitlements")
    prompt: Mapped["Prompt"] = relationship(back_populates="marketplace_entitlements")
    purchase: Mapped["PromptPurchase | None"] = relationship(back_populates="entitlement")


class PromptReview(Base):
    __tablename__ = "prompt_reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_purchase_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_purchases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    moderation_status: Mapped[ReviewModerationStatus] = mapped_column(
        Enum(ReviewModerationStatus, native_enum=False, length=32),
        nullable=False,
        default=ReviewModerationStatus.visible,
        index=True,
    )
    moderation_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    reported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    purchase: Mapped["PromptPurchase"] = relationship(back_populates="review")
    prompt: Mapped["Prompt"] = relationship(back_populates="marketplace_reviews")
    seller: Mapped["User | None"] = relationship(
        back_populates="marketplace_reviews_received",
        foreign_keys=[seller_user_id],
    )
    author: Mapped["User"] = relationship(
        back_populates="marketplace_reviews_written",
        foreign_keys=[author_user_id],
    )
    reports: Mapped[list["PromptReviewReport"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class PromptReviewReport(Base):
    __tablename__ = "prompt_review_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporter_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("review_id", "reporter_user_id", name="uq_prompt_review_reports_unique_reporter"),
    )

    review: Mapped["PromptReview"] = relationship(back_populates="reports")
    reporter: Mapped["User"] = relationship(back_populates="marketplace_review_reports")


class MarketplacePayout(Base):
    __tablename__ = "marketplace_payouts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[MarketplacePayoutStatus] = mapped_column(
        Enum(MarketplacePayoutStatus, native_enum=False, length=32),
        nullable=False,
        default=MarketplacePayoutStatus.requested,
        index=True,
    )
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchase_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    external_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    seller: Mapped["User | None"] = relationship(back_populates="marketplace_payouts")
    purchases: Mapped[list["PromptPurchase"]] = relationship(back_populates="payout")


class MarketplaceTransaction(Base):
    __tablename__ = "marketplace_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompt_purchases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind: Mapped[MarketplaceTransactionKind] = mapped_column(
        Enum(MarketplaceTransactionKind, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    purchase: Mapped["PromptPurchase | None"] = relationship(back_populates="ledger_entries")
    actor_user: Mapped["User | None"] = relationship(back_populates="marketplace_transactions")
    prompt: Mapped["Prompt | None"] = relationship()
