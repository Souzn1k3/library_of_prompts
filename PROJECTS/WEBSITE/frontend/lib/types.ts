export type PromptStatus = "draft" | "published" | "archived";

export type PromptTechnique =
  | "zero_shot"
  | "few_shot"
  | "chain_of_thought"
  | "other";

export type PromptDifficulty = "beginner" | "intermediate" | "advanced";
export type PromptOutputType = "text" | "code" | "structured";
export type ContributorTier = "new" | "verified" | "top";
export type CatalogAction = "open" | "buy" | "signin";

export type ModerationState = "none" | "pending" | "approved" | "rejected";

export type Category = {
  id: string;
  parent_id: string | null;
  slug: string;
  name: string;
  sort_order: number;
  is_restricted: boolean;
};

export type PromptListItem = {
  id: string;
  slug: string;
  title: string;
  summary: string | null;
  status: PromptStatus;
  technique: PromptTechnique;
  moderation_state: ModerationState;
  category_id: string;
  author_id: string | null;
  created_at: string;
  is_premium?: boolean;
  is_paid?: boolean;
  difficulty?: PromptDifficulty | null;
  output_type?: PromptOutputType | null;
  price?: PromptPrice | null;
  access?: PromptAccess | null;
  use_cases?: string[];
  model_compatibility?: string[];
  tags?: string[];
  save_count?: number;
  copy_count?: number;
  quality_score?: number;
  contributor_slug?: string | null;
  contributor_tier?: ContributorTier | null;
  contributor_reputation_score?: number | null;
  author_display_name?: string | null;
  author_rating_average?: number | null;
  author_rating_count?: number;
  recommendation_reason_key?: string | null;
};

export type PromptDetail = PromptListItem & {
  body: string;
  body_locked?: boolean;
  unlock_offer?: StoreUnlockOffer | null;
  reviews?: PromptReviewList | null;
};

export type PromptPrice = {
  price_rub: number;
  price_lumens: number;
  commission_percent: number;
};

export type PromptAccess = {
  has_access: boolean;
  is_owned?: boolean;
  source?: string | null;
  can_unlock_with_plan?: boolean;
  remaining_plan_unlocks?: number;
  monthly_plan_unlocks?: number;
  purchase_required?: boolean;
  catalog_action?: CatalogAction;
};

export type ReviewSort = "new" | "best";
export type ReviewModerationStatus = "visible" | "pending" | "hidden";
export type MarketplaceSettlementStatus = "pending" | "available" | "paid_out" | "refunded" | "disputed";
export type MarketplacePayoutStatus = "requested" | "processing" | "paid" | "failed" | "canceled";

export type PromptReview = {
  id: string;
  rating: number;
  text: string | null;
  author_user_id: string;
  author_display_name: string;
  author_slug: string | null;
  prompt_id: string;
  prompt_slug: string;
  prompt_title: string;
  created_at: string;
  updated_at: string;
  verified_purchase: boolean;
  moderation_status?: ReviewModerationStatus;
  moderation_reason?: string | null;
  reported_count?: number;
};

export type PromptReviewList = {
  seller_user_id?: string | null;
  rating_average?: number | null;
  rating_display?: number | null;
  review_count: number;
  sort: ReviewSort;
  items: PromptReview[];
};

export type AuthorSubmission = {
  id: string;
  slug: string;
  title: string;
  status: PromptStatus;
  moderation_state: ModerationState;
  moderation_notes?: string | null;
  moderated_at?: string | null;
  auto_approved?: boolean;
  feedback_hints?: string[];
  created_at: string;
};

export type ContributorStats = {
  total_submissions: number;
  approved_submissions: number;
  rejected_submissions: number;
  rejection_rate: number;
  total_saves: number;
  total_copies: number;
  mission_success_count: number;
  average_prompt_quality: number;
};

export type ContributorProfile = {
  user_id: string;
  slug: string;
  display_name: string;
  bio?: string | null;
  reputation_score: number;
  reputation_tier: ContributorTier;
  stats: ContributorStats;
  rating_average?: number | null;
  rating_display?: number | null;
  review_count?: number;
  sold_prompts_count?: number;
  purchases_count?: number;
  seller_revenue_rub?: number;
  seller_lumens_earned?: number;
  trust_indicators?: TrustIndicator[];
  recent_reviews?: PromptReview[];
  computed_at?: string | null;
};

export type ContributorTopItem = {
  user_id: string;
  slug: string;
  display_name: string;
  reputation_score: number;
  reputation_tier: ContributorTier;
  approved_submissions: number;
  total_saves: number;
};

export type PromptDiscoveryFilters = {
  use_cases: Array<{ slug: string; name: string }>;
  model_compatibility: Array<{ slug: string; name: string }>;
  tags: Array<{ slug: string; name: string }>;
  difficulties: string[];
  output_types: string[];
  sorts: string[];
};

export type DiscoverySections = {
  for_you?: PromptListItem[];
  trending: PromptListItem[];
  best_for_beginners: PromptListItem[];
  most_saved: PromptListItem[];
};

export type PromptRecommendationContext =
  | "home"
  | "dashboard"
  | "prompt_detail"
  | "after_save"
  | "after_lesson_complete";

export type PromptRecommendationStrategy =
  | "personalized"
  | "contextual"
  | "cold_start";

export type PromptRecommendationResponse = {
  context: PromptRecommendationContext;
  strategy: PromptRecommendationStrategy;
  items: PromptListItem[];
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type UserProfile = {
  id: string;
  email: string;
  display_name: string;
  role: string;
  plan_tier: string;
  mission_credits?: number;
  premium_unlock_until?: string | null;
  contributor_slug?: string | null;
  rating_average?: number | null;
  rating_display?: number | null;
  review_count?: number;
  sold_prompts_count?: number;
  purchases_count?: number;
  seller_revenue_rub?: number;
  seller_lumens_earned?: number;
  trust_indicators?: TrustIndicator[];
  created_at: string;
};

export type PlanRecord = {
  tier: string;
  name: string;
  description?: string | null;
  price_usd_month: number;
  price_rub_month: number;
  monthly_paid_prompt_limit: number;
  prompt_purchase_discount_percent: number;
  lumen_purchase_discount_percent: number;
  highlights: string[];
  full_features: string[];
  sort_order?: number;
  is_active?: boolean;
};

export type BillingStatus = {
  plan_tier: string;
  subscription_tier: string | null;
  provider: string | null;
  status: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  updated_at: string | null;
  paid_prompt_limit_total: number;
  paid_prompt_limit_remaining: number;
  prompt_purchase_discount_percent: number;
  lumen_purchase_discount_percent: number;
};

export type CheckoutSessionResult = {
  url: string;
  session_id: string | null;
};

export type OnboardingRole = "student" | "developer" | "other";
export type OnboardingGoal = "learning" | "solving_tasks" | "productivity";

export type OnboardingProfile = {
  role: OnboardingRole | null;
  goal: OnboardingGoal | null;
  ai_context: string | null;
  completed_at: string | null;
  skipped_at: string | null;
  first_win_prompt_id: string | null;
  first_win_completed_at: string | null;
  is_completed: boolean;
  is_skipped: boolean;
  needs_onboarding: boolean;
};

export type OnboardingStarterPrompt = {
  id: string;
  slug: string;
  title: string;
  summary: string | null;
  technique: string;
  category_id: string;
};

export type OnboardingStarterLesson = {
  id: string;
  slug: string;
  title: string;
  min_tier: string;
  locked: boolean;
};

export type OnboardingStarterAction = {
  prompt_id: string;
  prompt_slug: string;
  prompt_title: string;
  prompt_body: string;
  instruction: string;
};

export type OnboardingStarterPack = {
  prompts: OnboardingStarterPrompt[];
  lesson: OnboardingStarterLesson | null;
  action: OnboardingStarterAction | null;
};

export type OnboardingFirstWinResult = {
  profile: OnboardingProfile;
  economy: EconomyAction;
};

export type MissionActionType =
  | "copy_prompt"
  | "save_prompt"
  | "copy_or_save_prompt"
  | "lesson_completed"
  | "onboarding_first_win"
  | "manual_confirmation"
  | "daily_checkin"
  | "streak_activity"
  | "challenge_submission"
  | "multi_step"
  | "apply_prompt"
  | "store_purchase";

export type MissionType =
  | "learning"
  | "action"
  | "streak"
  | "challenge"
  | "progression"
  | "habit"
  | "progress"
  | "spend_linked";

export type MissionProgressStatus = "not_started" | "in_progress" | "completed";

export type MissionPromptRef = {
  id: string;
  slug: string;
  title: string;
  summary: string | null;
};

export type MissionLessonRef = {
  id: string;
  slug: string;
  title: string;
  min_tier: string;
  locked: boolean;
};

export type MissionRewardView = {
  badge: string | null;
  credits: number;
  premium_days: number;
  granted_at: string | null;
};

export type MissionNextStep = {
  label: string;
  href: string;
  action: string;
};

export type MissionRead = {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  objective: string;
  completion_condition: string;
  difficulty: "easy" | "standard" | "advanced" | "expert";
  mission_type: MissionType;
  action_type: MissionActionType;
  is_repeatable: boolean;
  repeat_interval_days: number;
  chain_id: string | null;
  chain_step: number;
  chain_total: number;
  chain_next_unlocked: boolean;
  adaptive_reason: string | null;
  synergy_bonus_preview: number;
  status: MissionProgressStatus;
  completion_count: number;
  progress_count: number;
  required_count: number;
  started_at: string | null;
  last_event_at: string | null;
  completed_at: string | null;
  available_again_at: string | null;
  prompts: MissionPromptRef[];
  lesson: MissionLessonRef | null;
  steps: MissionStepRead[];
  reward: MissionRewardView;
  next_step: MissionNextStep | null;
};

export type MissionStepRead = {
  id: string;
  title: string;
  description: string | null;
  action_type: MissionActionType;
  status: MissionProgressStatus;
  progress_count: number;
  required_count: number;
  reward_credits: number;
  prompt: MissionPromptRef | null;
  lesson: MissionLessonRef | null;
};

export type MissionRewardSummary = {
  credits: number;
  badges: string[];
  premium_unlock_until: string | null;
};

export type MissionListRead = {
  missions: MissionRead[];
  current_mission_slug: string | null;
  completed_count: number;
  total_count: number;
  rewards: MissionRewardSummary;
};

export type MissionCurrentRead = {
  current: MissionRead | null;
  next: MissionRead | null;
  latest_completed: MissionRead | null;
  completed_count: number;
  total_count: number;
  rewards: MissionRewardSummary;
};

export type CurrencyTransactionType =
  | "mission_reward"
  | "store_purchase"
  | "streak_bonus"
  | "first_purchase_bonus"
  | "manual_adjustment"
  | "refund"
  | "cashback_locked"
  | "cashback_unlocked"
  | "boost_purchase"
  | "upgrade_purchase"
  | "surprise_reward"
  | "rank_bonus"
  | "spend_streak_bonus"
  | "marketplace_purchase"
  | "marketplace_sale";

export type CurrencyTransaction = {
  id: string;
  amount: number;
  balance_after: number;
  reason: CurrencyTransactionType;
  context: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
};

export type WalletBenefit = {
  key: string;
  kind: string;
  metadata?: Record<string, unknown> | null;
  expires_at: string | null;
};

export type WalletPurchase = {
  id: string;
  item_slug: string;
  item_title: string;
  kind: StoreItemKind;
  price_paid: number;
  status: PurchaseStatus;
  metadata?: Record<string, unknown> | null;
  created_at: string;
};

export type WalletLockedReward = {
  id: string;
  amount: number;
  status: "pending" | "unlocked" | "expired";
  required_mission_count: number;
  completed_mission_count: number;
  unlock_by: string | null;
  created_at: string;
  metadata?: Record<string, unknown> | null;
};

export type WalletGoal = {
  layer: "short" | "mid" | "long" | string;
  key: string;
  title: string;
  description: string;
  progress: number;
  target: number;
  reward?: string | null;
  expires_at?: string | null;
};

export type WalletStreakMilestone = {
  streak: number;
  reward: number;
};

export type WalletEconomyConfig = {
  daily_ladder_rewards: number[];
  streak_milestones: WalletStreakMilestone[];
  near_miss_max_delta: number;
};

export type WalletRead = {
  balance: number;
  currency: string;
  currency_name: string;
  currency_symbol: string;
  total_earned: number;
  total_spent: number;
  current_streak: number;
  best_streak: number;
  spend_streak_days: number;
  spend_streak_mult: number;
  streak_freeze_tokens: number;
  last_check_in_at: string | null;
  check_in_available: boolean;
  pending_locked_rewards: WalletLockedReward[];
  rank_points: number;
  rank_level: number;
  rank_next_threshold: number;
  owned_value_generated: number;
  goals: WalletGoal[];
  economy_config?: WalletEconomyConfig | null;
  premium_unlock_until: string | null;
  active_benefits: WalletBenefit[];
  recent_purchases: WalletPurchase[];
  recent: CurrencyTransaction[];
};

export type StoreItemKind =
  | "starter"
  | "subscription_discount"
  | "premium_pass"
  | "premium_prompt_unlock"
  | "prompt_bundle"
  | "boost"
  | "future";

export type StorePriceBand = "entry" | "core" | "mid" | "premium";

export type StoreItem = {
  id: string;
  slug: string;
  title: string;
  description: string | null;
  price: number;
  kind: StoreItemKind;
  availability: number | null;
  metadata?: Record<string, unknown> | null;
  is_active: boolean;
  owned: boolean;
  is_affordable: boolean;
  remaining_lumens: number;
  progress_ratio: number;
  price_band: StorePriceBand;
  tags: string[];
  starter_type?: string | null;
  is_limited_offer: boolean;
  offer_ends_at: string | null;
  offer_reason: string | null;
  dynamic_offer: boolean;
  upgrade_tier: number;
  max_tier: number;
  next_upgrade_cost: number | null;
  boost_pct: number | null;
  boost_missions_left: number | null;
  near_miss_delta: number;
};

export type PurchaseStatus = "pending" | "completed" | "refunded" | "failed" | "canceled";

export type PurchaseRead = {
  id: string;
  status: PurchaseStatus;
  price_paid: number;
  metadata?: Record<string, unknown> | null;
  client_token?: string | null;
  item: StoreItem;
  created_at: string;
};

export type StoreReward = {
  kind: string;
  title: string;
  description: string | null;
  amount: number | null;
  metadata?: Record<string, unknown> | null;
};

export type EconomyAction = {
  wallet: WalletRead | null;
  available_items: StoreItem[];
  newly_affordable_items: StoreItem[];
  best_item: StoreItem | null;
  balance_delta: number;
  completed_mission_slugs: string[];
  near_miss_message?: string | null;
};

export type PurchaseResult = {
  purchase: PurchaseRead;
  wallet: WalletRead;
  available_items: StoreItem[];
  newly_affordable_items: StoreItem[];
  best_item: StoreItem | null;
  first_purchase_reward: StoreReward | null;
  locked_cashback_reward: StoreReward | null;
  second_purchase_challenge_reward: StoreReward | null;
};

export type LessonCompletionResult = EconomyAction;
export type PromptActionResult = EconomyAction;

export type TrustIndicator = {
  key: string;
  level: "info" | "good" | "strong";
};

export type PromptMarketplacePurchase = {
  id: string;
  prompt_id: string;
  prompt_slug: string;
  prompt_title: string;
  seller_user_id: string | null;
  status: PurchaseStatus;
  payment_method: "included_limit" | "lumens" | "stripe" | "legacy_store";
  price_rub: number;
  price_lumens: number;
  settlement_status?: MarketplaceSettlementStatus;
  settlement_available_at?: string | null;
  paid_out_at?: string | null;
  created_at: string;
  completed_at: string | null;
  can_review: boolean;
  review?: PromptReview | null;
};

export type MarketplacePayout = {
  id: string;
  currency_code: string;
  status: MarketplacePayoutStatus;
  total_amount: number;
  purchase_count: number;
  external_reference?: string | null;
  requested_at: string;
  paid_at?: string | null;
};

export type SellerMarketplaceSummary = {
  rating_average: number | null;
  rating_display: number | null;
  review_count: number;
  sold_prompts_count: number;
  purchases_count: number;
  seller_revenue_rub: number;
  seller_lumens_earned: number;
  pending_balance_rub: number;
  available_balance_rub: number;
  paid_out_rub: number;
  refunded_balance_rub: number;
  disputed_balance_rub: number;
  pending_balance_lumens: number;
  available_balance_lumens: number;
  paid_out_lumens: number;
  refunded_balance_lumens: number;
  disputed_balance_lumens: number;
  platform_commission_rub: number;
  platform_commission_lumens: number;
  clawback_due_rub: number;
  clawback_due_lumens: number;
  payout_eligible: boolean;
  trust_indicators: TrustIndicator[];
  recent_reviews: PromptReview[];
  recent_payouts: MarketplacePayout[];
};

export type MarketplaceOverview = {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  reviews: PromptReview[];
  payouts: MarketplacePayout[];
};

export type StoreUnlockOffer = {
  item_slug: string;
  item_title: string;
  price: number;
  currency: string;
  kind: StoreItemKind;
};

export type LessonListItem = {
  id: string;
  slug: string;
  title: string;
  min_tier: string;
  sort_order: number;
  created_at: string;
  locked: boolean;
};

export type PopularLessonItem = LessonListItem & {
  completion_count: number;
};

export type LessonDetail = LessonListItem & {
  body: string;
  body_locked?: boolean;
};
