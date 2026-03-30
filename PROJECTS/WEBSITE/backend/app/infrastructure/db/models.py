import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
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


class CurrencyTransactionType(str, enum.Enum):
    mission_reward = "mission_reward"
    store_purchase = "store_purchase"
    streak_bonus = "streak_bonus"
    manual_adjustment = "manual_adjustment"
    refund = "refund"


class StoreItemKind(str, enum.Enum):
    subscription_discount = "subscription_discount"
    premium_pass = "premium_pass"
    premium_prompt_unlock = "premium_prompt_unlock"
    prompt_bundle = "prompt_bundle"
    future = "future"


class PurchaseStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    refunded = "refunded"


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
