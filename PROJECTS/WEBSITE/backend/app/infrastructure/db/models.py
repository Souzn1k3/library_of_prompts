import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Date,
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserRole(str, enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class PlanTier(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class PromptStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class PromptTechnique(str, enum.Enum):
    zero_shot = "zero_shot"
    few_shot = "few_shot"
    chain_of_thought = "chain_of_thought"
    other = "other"


class PromptDifficulty(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class PromptOutputType(str, enum.Enum):
    text = "text"
    code = "code"
    structured = "structured"


class ModerationState(str, enum.Enum):
    none_ = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BillingProvider(str, enum.Enum):
    stripe = "stripe"
    mock = "mock"


class SubscriptionStatus(str, enum.Enum):
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"


class OnboardingRole(str, enum.Enum):
    student = "student"
    developer = "developer"
    other = "other"


class OnboardingGoal(str, enum.Enum):
    learning = "learning"
    solving_tasks = "solving_tasks"
    productivity = "productivity"


class MissionActionType(str, enum.Enum):
    copy_prompt = "copy_prompt"
    save_prompt = "save_prompt"
    copy_or_save_prompt = "copy_or_save_prompt"
    lesson_completed = "lesson_completed"
    onboarding_first_win = "onboarding_first_win"
    manual_confirmation = "manual_confirmation"
    daily_checkin = "daily_checkin"
    streak_activity = "streak_activity"
    challenge_submission = "challenge_submission"
    multi_step = "multi_step"
    apply_prompt = "apply_prompt"
    store_purchase = "store_purchase"


class MissionProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class MissionRewardType(str, enum.Enum):
    badge = "badge"
    credits = "credits"
    premium_unlock = "premium_unlock"


class MissionDifficulty(str, enum.Enum):
    easy = "easy"
    standard = "standard"
    advanced = "advanced"
    expert = "expert"


class MissionType(str, enum.Enum):
    learning = "learning"
    action = "action"
    streak = "streak"
    challenge = "challenge"
    progression = "progression"
    habit = "habit"
    progress = "progress"
    spend_linked = "spend_linked"


class CurrencyTransactionType(str, enum.Enum):
    mission_reward = "mission_reward"
    store_purchase = "store_purchase"
    streak_bonus = "streak_bonus"
    first_purchase_bonus = "first_purchase_bonus"
    manual_adjustment = "manual_adjustment"
    refund = "refund"
    marketplace_purchase = "marketplace_purchase"
    marketplace_sale = "marketplace_sale"
    cashback_locked = "cashback_locked"
    cashback_unlocked = "cashback_unlocked"
    boost_purchase = "boost_purchase"
    upgrade_purchase = "upgrade_purchase"
    surprise_reward = "surprise_reward"
    rank_bonus = "rank_bonus"
    spend_streak_bonus = "spend_streak_bonus"


class StoreItemKind(str, enum.Enum):
    starter = "starter"
    subscription_discount = "subscription_discount"
    premium_pass = "premium_pass"
    premium_prompt_unlock = "premium_prompt_unlock"
    prompt_bundle = "prompt_bundle"
    boost = "boost"
    future = "future"


class LockedRewardStatus(str, enum.Enum):
    pending = "pending"
    unlocked = "unlocked"
    expired = "expired"


class BoostStatus(str, enum.Enum):
    active = "active"
    exhausted = "exhausted"
    expired = "expired"


class PurchaseStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"
    failed = "failed"
    canceled = "canceled"


class PromptAccessSource(str, enum.Enum):
    free = "free"
    author = "author"
    staff = "staff"
    subscription_limit = "subscription_limit"
    direct_lumens = "direct_lumens"
    direct_money = "direct_money"
    legacy_store = "legacy_store"


class PromptPaymentMethod(str, enum.Enum):
    included_limit = "included_limit"
    lumens = "lumens"
    stripe = "stripe"
    legacy_store = "legacy_store"


class MarketplaceTransactionKind(str, enum.Enum):
    buyer_charge = "buyer_charge"
    seller_credit = "seller_credit"
    platform_fee = "platform_fee"
    refund = "refund"
    included_unlock = "included_unlock"
    seller_available = "seller_available"
    seller_payout = "seller_payout"
    seller_reversal = "seller_reversal"
    dispute_hold = "dispute_hold"


class MarketplaceSettlementStatus(str, enum.Enum):
    pending = "pending"
    available = "available"
    paid_out = "paid_out"
    refunded = "refunded"
    disputed = "disputed"


class MarketplacePayoutStatus(str, enum.Enum):
    requested = "requested"
    processing = "processing"
    paid = "paid"
    failed = "failed"
    canceled = "canceled"


class ReviewModerationStatus(str, enum.Enum):
    visible = "visible"
    pending = "pending"
    hidden = "hidden"


class ContributorTier(str, enum.Enum):
    new = "new"
    verified = "verified"
    top = "top"


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
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User | None"] = relationship(back_populates="analytics_events")


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


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_restricted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    parent: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_id],
    )
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="category")


class UseCase(Base):
    __tablename__ = "use_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptUseCase"]] = relationship(
        back_populates="use_case",
        cascade="all, delete-orphan",
    )


class ModelCompatibility(Base):
    __tablename__ = "model_compatibilities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptModelCompatibility"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    prompt_links: Mapped[list["PromptTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[PromptStatus] = mapped_column(
        Enum(PromptStatus), nullable=False, default=PromptStatus.draft
    )
    technique: Mapped[PromptTechnique] = mapped_column(
        Enum(PromptTechnique), nullable=False, default=PromptTechnique.other
    )
    difficulty: Mapped[PromptDifficulty | None] = mapped_column(
        Enum(PromptDifficulty, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    output_type: Mapped[PromptOutputType | None] = mapped_column(
        Enum(PromptOutputType, native_enum=False, length=32),
        nullable=True,
        index=True,
    )
    moderation_state: Mapped[ModerationState] = mapped_column(
        Enum(ModerationState), nullable=False, default=ModerationState.none_
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    moderation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    moderated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    legacy_bot_prompt_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    legacy_bot_category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    legacy_bot_subcategory: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    content_language: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    category: Mapped["Category"] = relationship(back_populates="prompts")
    author: Mapped["User | None"] = relationship(back_populates="prompts", foreign_keys=[author_id])
    moderated_by: Mapped["User | None"] = relationship(foreign_keys=[moderated_by_id])
    saved_by_links: Mapped[list["SavedPrompt"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    stats: Mapped["PromptStats | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    quality_metrics: Mapped["PromptQualityMetric | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    use_case_links: Mapped[list["PromptUseCase"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    model_links: Mapped[list["PromptModelCompatibility"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    tag_links: Mapped[list["PromptTag"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    mission_links: Mapped[list["LessonMissionPrompt"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    pricing: Mapped["PromptPrice | None"] = relationship(
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )
    marketplace_entitlements: Mapped[list["PromptEntitlement"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    marketplace_purchases: Mapped[list["PromptPurchase"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    marketplace_reviews: Mapped[list["PromptReview"]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


class PromptStats(Base):
    __tablename__ = "prompt_stats"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    save_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    copy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="stats")


class PromptQualityMetric(Base):
    __tablename__ = "prompt_quality_metrics"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    unique_savers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    copy_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mission_success_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="quality_metrics")


class PromptUseCase(Base):
    __tablename__ = "prompt_use_cases"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    use_case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("use_cases.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="use_case_links")
    use_case: Mapped["UseCase"] = relationship(back_populates="prompt_links")


class PromptModelCompatibility(Base):
    __tablename__ = "prompt_model_compatibilities"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_compatibilities.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="model_links")
    model: Mapped["ModelCompatibility"] = relationship(back_populates="prompt_links")


class PromptTag(Base):
    __tablename__ = "prompt_tags"

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt: Mapped["Prompt"] = relationship(back_populates="tag_links")
    tag: Mapped["Tag"] = relationship(back_populates="prompt_links")


class SavedPrompt(Base):
    __tablename__ = "saved_prompts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="saved_prompt_links")
    prompt: Mapped["Prompt"] = relationship(back_populates="saved_by_links")

# Keep the public import surface in this module while isolating the densest
# mission/progression schema block in a private sibling.
from ._mission_models import (  # noqa: E402
    Lesson,
    LessonMission,
    LessonMissionPrompt,
    MissionCompletionEvent,
    MissionStep,
    UserMissionProgress,
    UserMissionRewardGrant,
    UserMissionStepProgress,
)


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
