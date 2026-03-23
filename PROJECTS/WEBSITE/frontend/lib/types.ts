export type PromptStatus = "draft" | "published" | "archived";

export type PromptTechnique =
  | "zero_shot"
  | "few_shot"
  | "chain_of_thought"
  | "other";

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
};

export type PromptDetail = PromptListItem & {
  body: string;
  body_locked?: boolean;
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type UserProfile = {
  id: string;
  email: string;
  display_name: string;
  role: string;
  plan_tier: string;
  created_at: string;
};

export type PlanRecord = {
  tier: string;
  name: string;
  price_usd_month: number;
  features: string[];
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

export type LessonDetail = LessonListItem & {
  body: string;
  body_locked?: boolean;
};
