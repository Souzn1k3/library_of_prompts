import type { EconomyAction } from "./economy";

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

export type OnboardingFirstWinResult = {
  profile: OnboardingProfile;
  economy: EconomyAction;
};
