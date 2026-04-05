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

export type StoreItemKind =
  | "starter"
  | "subscription_discount"
  | "premium_pass"
  | "premium_prompt_unlock"
  | "prompt_bundle"
  | "boost"
  | "future";

export type PurchaseStatus = "pending" | "completed" | "refunded" | "failed" | "canceled";

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

export type StoreUnlockOffer = {
  item_slug: string;
  item_title: string;
  price: number;
  currency: string;
  kind: StoreItemKind;
};
