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

export type ScenarioHomeAggregateRead = {
  generated_at: string;
  featured: PromptListItem[];
  recommended: PromptListItem[];
  retention: PromptListItem[];
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
