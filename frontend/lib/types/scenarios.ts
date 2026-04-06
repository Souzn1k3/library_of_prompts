import type { PromptListItem } from "./catalog";

export type ScenarioWorkspaceAction =
  | "open"
  | "run"
  | "copy"
  | "share"
  | "save"
  | "unsave"
  | "unfinished_update"
  | "unfinished_clear";

export type ScenarioWorkspaceItem = {
  prompt: PromptListItem;
  is_saved: boolean;
  unfinished_task: string | null;
  run_count: number;
  copy_count: number;
  share_count: number;
  last_used_at: string;
  last_run_at: string | null;
  last_opened_at: string | null;
};

export type ScenarioWorkspaceRead = {
  recent: ScenarioWorkspaceItem[];
  saved: ScenarioWorkspaceItem[];
  unfinished: ScenarioWorkspaceItem[];
};

export type ScenarioWorkspaceTrackRequest = {
  prompt_slug: string;
  action: ScenarioWorkspaceAction;
  task_input?: string | null;
};

export type ScenarioRunEventRead = {
  prompt_id: string;
  prompt_slug: string;
  action: ScenarioWorkspaceAction;
  tracked_at: string;
  workspace: ScenarioWorkspaceRead;
};

export type ScenarioWorkspaceLimitsRead = {
  recent_limit: number;
  saved_limit: number;
  unfinished_limit: number;
};

export type ScenarioLoopHintsRead = {
  core_loop_steps: string[];
  pro_capabilities: string[];
  free_demo_runs_per_scenario: number;
};

export type ScenarioPackRead = {
  id: string;
  title: string;
  description: string;
  outcome: string;
  prompt_slugs: string[];
  prompts: PromptListItem[];
  cta_prompt_slug: string | null;
};

export type ScenarioChainStepRead = {
  position: number;
  prompt_slug: string;
  title: string;
  goal: string;
};

export type ScenarioChainRead = {
  id: string;
  title: string;
  description: string;
  steps: ScenarioChainStepRead[];
};

export type ScenarioNextStepRead = {
  source_prompt_slug: string | null;
  next_prompt_slug: string;
  reason: string;
  confidence: number;
};

export type ScenarioReturnTriggerRead = {
  trigger_key: string;
  label: string;
  count: number;
  href: string;
};

export type ScenarioPricingPlanRead = {
  tier: "free" | "starter" | "pro" | "enterprise";
  price_monthly_usd: number;
  headline: string;
  highlights: string[];
};

export type ScenarioShowcaseRead = {
  share_id: string;
  prompt_slug: string | null;
  blueprint_id: string | null;
  title: string;
  excerpt: string;
  output_preview: string;
  visibility: string;
  upvotes: number;
  created_at: string;
};

export type ScenarioHomeAggregateRead = {
  generated_at: string;
  featured: PromptListItem[];
  recommended: PromptListItem[];
  retention: PromptListItem[];
  packs: ScenarioPackRead[];
  chains: ScenarioChainRead[];
  next_steps: ScenarioNextStepRead[];
  return_triggers: ScenarioReturnTriggerRead[];
  showcase: ScenarioShowcaseRead[];
  pricing_plans: ScenarioPricingPlanRead[];
  workspace: ScenarioWorkspaceRead | null;
  workspace_limits: ScenarioWorkspaceLimitsRead;
  loop_hints: ScenarioLoopHintsRead;
};

export type ScenarioDemoRunStatusRead = {
  prompt_slug: string;
  is_authenticated: boolean;
  is_pro: boolean;
  free_cap: number | null;
  used_runs: number;
  remaining_runs: number | null;
  cap_reached: boolean;
  allowed: boolean;
  reason: string | null;
  upgrade_hint: string | null;
  guest_session_id: string | null;
  bonus_runs_remaining: number | null;
};

export type ScenarioDemoRunTrackRequest = {
  prompt_slug: string;
  task_input?: string | null;
};

export type ScenarioDemoRunTrackRead = {
  executed: boolean;
  status: ScenarioDemoRunStatusRead;
  workspace: ScenarioWorkspaceRead | null;
};

export type ScenarioGameStateRead = {
  source: string;
  pending_tokens: number;
  claimable_tokens: number;
  claimed_tokens_today: number;
  daily_cap: number;
  daily_cap_remaining: number;
  cooldown_minutes: number;
  needs_auth_to_claim: boolean;
};

export type ScenarioGameEarnRequest = {
  event_id: string;
  challenge_id: string;
  choice_index: number;
};

export type ScenarioGameEarnRead = {
  accepted: boolean;
  reason: string;
  reward_tokens: number;
  pending_tokens: number;
  daily_cap_remaining: number;
  cooldown_seconds: number | null;
  source: string;
};

export type ScenarioGameClaimRequest = {
  claim_id?: string | null;
};

export type ScenarioGameClaimRead = {
  claim_id: string;
  source: string;
  applied: boolean;
  claimed_tokens: number;
  pending_tokens_after: number;
  balance_after: number | null;
};

export type ScenarioTokenBoostPurchaseRequest = {
  prompt_slug: string;
};

export type ScenarioTokenBoostPurchaseRead = {
  prompt_slug: string;
  applied_bonus_runs: number;
  bonus_runs_remaining: number;
  token_cost: number;
  balance_after: number | null;
  is_pro: boolean;
};

export type ScenarioShowcaseCreateRequest = {
  share_id?: string;
  prompt_slug?: string | null;
  blueprint_id?: string | null;
  title: string;
  excerpt: string;
  output_preview: string;
  visibility?: "public" | "unlisted";
};

export type ScenarioShowcaseUpvoteRequest = {
  share_id: string;
};

export type ScenarioBlueprintWrite = {
  slug: string;
  title: string;
  summary?: string | null;
  category: "utility" | "learning" | "productivity" | "entertainment" | "growth";
  input_schema?: Record<string, unknown> | null;
  context_text?: string | null;
  logic_text?: string | null;
  output_text?: string | null;
  run_instructions?: string | null;
  source_prompt_slug?: string | null;
  visibility?: "private" | "team" | "public" | "marketplace";
  is_premium?: boolean;
  token_price?: number | null;
};

export type ScenarioBlueprintPatch = Partial<ScenarioBlueprintWrite>;

export type ScenarioBlueprintRead = {
  id: string;
  owner_user_id: string;
  slug: string;
  title: string;
  summary: string | null;
  category: string;
  visibility: string;
  is_published: boolean;
  is_premium: boolean;
  token_price: number | null;
  input_schema: Record<string, unknown> | null;
  context_text: string | null;
  logic_text: string | null;
  output_text: string | null;
  run_instructions: string | null;
  usage_count: number;
  fork_count: number;
  like_count: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type ScenarioBlueprintPublishRead = {
  blueprint: ScenarioBlueprintRead;
  creator_reward_tokens: number;
  creator_reward_applied: boolean;
};

export type ScenarioBlueprintShareWrite = {
  member_email: string;
  can_edit?: boolean;
};

export type ScenarioBlueprintShareRead = {
  blueprint_id: string;
  owner_user_id: string;
  member_user_id: string;
  can_edit: boolean;
  created_at: string;
};

export type ScenarioMarketplaceForkRead = {
  source_blueprint_id: string;
  forked_blueprint: ScenarioBlueprintRead;
  token_spent: number;
  balance_after: number | null;
  creator_reward_applied: boolean;
};

export type ScenarioWorkflowWrite = {
  name: string;
  description?: string | null;
  visibility?: "private" | "team" | "public";
  step_blueprint_ids: string[];
};

export type ScenarioWorkflowRead = {
  id: string;
  owner_user_id: string;
  name: string;
  description: string | null;
  visibility: string;
  step_blueprint_ids: string[];
  created_at: string;
  updated_at: string;
};

export type ScenarioWorkflowRunStartWrite = {
  context?: Record<string, unknown> | null;
};

export type ScenarioWorkflowRunRead = {
  id: string;
  workflow_id: string;
  status: string;
  current_step: number;
  completed_steps: number;
  total_steps: number;
  next_blueprint_id: string | null;
  completed_at: string | null;
  last_active_at: string;
};

export type ScenarioWorkflowRunAdvanceRead = {
  run: ScenarioWorkflowRunRead;
  is_completed: boolean;
  next_blueprint_id: string | null;
};
