export type PromptStatus = "draft" | "published" | "archived";

export type PromptTechnique =
  | "zero_shot"
  | "few_shot"
  | "chain_of_thought"
  | "other";

export type PromptDifficulty = "beginner" | "intermediate" | "advanced";
export type PromptOutputType = "text" | "code" | "structured";
export type ContributorTier = "new" | "verified" | "top";

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
  difficulty?: PromptDifficulty | null;
  output_type?: PromptOutputType | null;
  use_cases?: string[];
  model_compatibility?: string[];
  tags?: string[];
  save_count?: number;
  copy_count?: number;
  quality_score?: number;
  contributor_slug?: string | null;
  contributor_tier?: ContributorTier | null;
  contributor_reputation_score?: number | null;
  recommendation_reason_key?: string | null;
};

export type PromptDetail = PromptListItem & {
  body: string;
  body_locked?: boolean;
  unlock_offer?: StoreUnlockOffer | null;
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
  created_at: string;
};

export type PlanRecord = {
  tier: string;
  name: string;
  description?: string | null;
  price_usd_month: number;
  features: string[];
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
  | "apply_prompt";

export type MissionType = "learning" | "action" | "streak" | "challenge" | "progression";

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
  | "manual_adjustment"
  | "refund";

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

export type WalletRead = {
  balance: number;
  currency: string;
  currency_name: string;
  currency_symbol: string;
  total_earned: number;
  total_spent: number;
  current_streak: number;
  best_streak: number;
  last_check_in_at: string | null;
  check_in_available: boolean;
  premium_unlock_until: string | null;
  active_benefits: WalletBenefit[];
  recent_purchases: WalletPurchase[];
  recent: CurrencyTransaction[];
};

export type StoreItemKind =
  | "subscription_discount"
  | "premium_pass"
  | "premium_prompt_unlock"
  | "prompt_bundle"
  | "future";

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
};

export type PurchaseStatus = "pending" | "completed" | "refunded";

export type PurchaseRead = {
  id: string;
  status: PurchaseStatus;
  price_paid: number;
  metadata?: Record<string, unknown> | null;
  client_token?: string | null;
  item: StoreItem;
  created_at: string;
};

export type PurchaseResult = {
  purchase: PurchaseRead;
  wallet: WalletRead;
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
