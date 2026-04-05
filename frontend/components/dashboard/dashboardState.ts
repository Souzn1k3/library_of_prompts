import type {
  AuthorSubmission,
  BillingStatus,
  LearningCourseDetail,
  LearningMyModules,
  MissionCurrentRead,
  OnboardingProfile,
  OnboardingStarterPack,
  PromptListItem,
  WalletRead,
} from "@/lib/types";

import type { DashboardLoadSnapshot } from "./dashboardDataLoader";

export type DashboardState = {
  items: PromptListItem[] | null;
  recommended: PromptListItem[];
  submissions: AuthorSubmission[];
  error: string | null;
  billing: BillingStatus | null;
  wallet: WalletRead | null;
  missionCurrent: MissionCurrentRead | null;
  onboardingProfile: OnboardingProfile | null;
  starterPack: OnboardingStarterPack | null;
  learningMy: LearningMyModules | null;
  learningCourse: LearningCourseDetail | null;
};

export function createEmptyDashboardState(): DashboardState {
  return {
    items: null,
    recommended: [],
    submissions: [],
    error: null,
    billing: null,
    wallet: null,
    missionCurrent: null,
    onboardingProfile: null,
    starterPack: null,
    learningMy: null,
    learningCourse: null,
  };
}

export function dashboardStateFromSnapshot(snapshot: DashboardLoadSnapshot): DashboardState {
  return {
    items: snapshot.items,
    recommended: snapshot.recommended,
    submissions: snapshot.submissions,
    error: snapshot.error,
    billing: snapshot.billing,
    wallet: snapshot.wallet,
    missionCurrent: snapshot.missionCurrent,
    onboardingProfile: snapshot.onboardingProfile,
    starterPack: snapshot.starterPack,
    learningMy: snapshot.learningMy,
    learningCourse: null,
  };
}

