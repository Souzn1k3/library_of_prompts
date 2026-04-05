import enum


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
