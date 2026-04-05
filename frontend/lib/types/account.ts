import type { TrustIndicator } from "./shared";

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
