import type { PromptReview } from "./marketplace";
import type { TrustIndicator } from "./shared";

export type ContributorTier = "new" | "verified" | "top";

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
