import type { ContributorTier } from "./contributors";
import type { StoreUnlockOffer } from "./economy";
import type { PromptReviewList } from "./marketplace";

export type PromptStatus = "draft" | "published" | "archived";

export type PromptTechnique =
  | "zero_shot"
  | "few_shot"
  | "chain_of_thought"
  | "other";

export type PromptDifficulty = "beginner" | "intermediate" | "advanced";
export type PromptOutputType = "text" | "code" | "structured";
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
