"use client";

import { ApiRequestError } from "@/lib/api";
import {
  fetchBillingStatus,
  fetchCurrentMission,
  fetchLearningMyModules,
  fetchMySubmissions,
  fetchOnboardingProfile,
  fetchOnboardingStarterPack,
  fetchPromptRecommendations,
  fetchSavedPrompts,
  fetchWallet,
} from "@/lib/client-api";
import type { TranslationKey } from "@/lib/i18n";
import type {
  AuthorSubmission,
  BillingStatus,
  LearningMyModules,
  MissionCurrentRead,
  OnboardingProfile,
  OnboardingStarterPack,
  PromptListItem,
  WalletRead,
} from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

export type DashboardLoadSnapshot = {
  unauthorized: boolean;
  error: string | null;
  items: PromptListItem[] | null;
  recommended: PromptListItem[];
  submissions: AuthorSubmission[];
  billing: BillingStatus | null;
  wallet: WalletRead | null;
  onboardingProfile: OnboardingProfile | null;
  starterPack: OnboardingStarterPack | null;
  missionCurrent: MissionCurrentRead | null;
  learningMy: LearningMyModules | null;
};

const DASHBOARD_RECOMMENDATION_LIMIT = 4;

function fallbackFailedSnapshot(error: string): DashboardLoadSnapshot {
  return {
    unauthorized: false,
    error,
    items: [],
    recommended: [],
    submissions: [],
    billing: null,
    wallet: null,
    onboardingProfile: null,
    starterPack: null,
    missionCurrent: null,
    learningMy: null,
  };
}

export async function loadDashboardSnapshot(t: Translate): Promise<DashboardLoadSnapshot> {
  const [
    savedResult,
    recommendedResult,
    billingResult,
    walletResult,
    submissionsResult,
    onboardingResult,
    starterResult,
    missionResult,
    learningMyResult,
  ] = await Promise.allSettled([
    fetchSavedPrompts(),
    fetchPromptRecommendations({ context: "dashboard", limit: DASHBOARD_RECOMMENDATION_LIMIT }),
    fetchBillingStatus(),
    fetchWallet(),
    fetchMySubmissions(),
    fetchOnboardingProfile(),
    fetchOnboardingStarterPack(),
    fetchCurrentMission(),
    fetchLearningMyModules(),
  ]);

  const requiredFailures = [savedResult, billingResult, submissionsResult].filter(
    (result): result is PromiseRejectedResult => result.status === "rejected",
  );
  if (requiredFailures.length > 0) {
    const reason = requiredFailures[0].reason;
    if (reason instanceof ApiRequestError && reason.status === 401) {
      return {
        unauthorized: true,
        error: null,
        items: null,
        recommended: [],
        submissions: [],
        billing: null,
        wallet: null,
        onboardingProfile: null,
        starterPack: null,
        missionCurrent: null,
        learningMy: null,
      };
    }
    return fallbackFailedSnapshot(
      reason instanceof ApiRequestError ? reason.message : t("dashboard.loadError"),
    );
  }

  if (
    savedResult.status !== "fulfilled" ||
    billingResult.status !== "fulfilled" ||
    submissionsResult.status !== "fulfilled"
  ) {
    return fallbackFailedSnapshot(t("dashboard.loadError"));
  }

  return {
    unauthorized: false,
    error: null,
    items: savedResult.value,
    recommended: recommendedResult.status === "fulfilled" ? recommendedResult.value.items : [],
    submissions: submissionsResult.value,
    billing: billingResult.value,
    wallet: walletResult.status === "fulfilled" ? walletResult.value : null,
    onboardingProfile: onboardingResult.status === "fulfilled" ? onboardingResult.value : null,
    starterPack: starterResult.status === "fulfilled" ? starterResult.value : null,
    missionCurrent: missionResult.status === "fulfilled" ? missionResult.value : null,
    learningMy: learningMyResult.status === "fulfilled" ? learningMyResult.value : null,
  };
}

export function selectLearningCourseSlug(learningSummary: LearningMyModules | null): string | null {
  return (
    learningSummary?.active_courses[0]?.slug ??
    learningSummary?.completed_courses[0]?.slug ??
    null
  );
}
