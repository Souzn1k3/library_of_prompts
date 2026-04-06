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
