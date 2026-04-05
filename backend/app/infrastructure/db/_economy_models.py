from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Date,
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._enums import BoostStatus, CurrencyTransactionType, LockedRewardStatus, PurchaseStatus, StoreItemKind
from ._user_model import User
from .base import Base


class UserCurrencyBalance(Base):
    __tablename__ = "user_currency_balances"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    spend_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_spend_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    streak_freeze_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    surprise_miss_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    owned_value_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    catchup_boost_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    catchup_boost_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    second_purchase_challenge_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    second_purchase_challenge_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    second_purchase_challenge_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="currency_balance")


class CurrencyTransaction(Base):
    __tablename__ = "currency_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[CurrencyTransactionType] = mapped_column(
        Enum(CurrencyTransactionType, native_enum=False, length=40),
        nullable=False,
        index=True,
    )
    context: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="currency_transactions")


class StoreItem(Base):
    __tablename__ = "store_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kind: Mapped[StoreItemKind] = mapped_column(
        Enum(StoreItemKind, native_enum=False, length=40),
        nullable=False,
        default=StoreItemKind.premium_pass,
    )
    availability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    purchases: Mapped[list["UserPurchase"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
    )


class UserPurchase(Base):
    __tablename__ = "user_purchases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("store_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus, native_enum=False, length=32),
        nullable=False,
        default=PurchaseStatus.completed,
        index=True,
    )
    client_token: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True, index=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="purchases")
    item: Mapped["StoreItem"] = relationship(back_populates="purchases")


class UserLockedReward(Base):
    __tablename__ = "user_locked_rewards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_purchases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_mission_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    completed_mission_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[LockedRewardStatus] = mapped_column(
        Enum(LockedRewardStatus, native_enum=False, length=24),
        nullable=False,
        default=LockedRewardStatus.pending,
        index=True,
    )
    unlock_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="locked_rewards")
    source_purchase: Mapped["UserPurchase | None"] = relationship()


class UserActiveBoost(Base):
    __tablename__ = "user_active_boosts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_purchases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    boost_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    missions_total: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    missions_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[BoostStatus] = mapped_column(
        Enum(BoostStatus, native_enum=False, length=24),
        nullable=False,
        default=BoostStatus.active,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
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

    user: Mapped["User"] = relationship(back_populates="active_boosts")
    source_purchase: Mapped["UserPurchase | None"] = relationship()


class EconomyDailyKpi(Base):
    __tablename__ = "economy_daily_kpis"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    experiment_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    cohort: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_purchase_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    second_purchase_48h_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    second_purchase_48h_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    d1_retention_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    d7_retention_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lmn_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lmn_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lmn_spent_earned_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    median_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    store_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    store_purchases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    store_conversion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    wallet_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mission_completions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_time_to_first_purchase_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_time_to_second_purchase_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
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
            "date",
            "experiment_name",
            "cohort",
            name="uq_economy_daily_kpis_day_experiment_cohort",
        ),
    )
