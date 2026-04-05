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
