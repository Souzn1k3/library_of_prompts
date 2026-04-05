"use client";

import { useMemo } from "react";

import { billingStatusLabel, normalizeStarterPrompt } from "@/components/dashboard/helpers";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getTierTranslationKey, type Language, type TranslationKey } from "@/lib/i18n";
import { getMissionPresentation } from "@/lib/missionPresentation";
import type {
  AuthorSubmission,
  BillingStatus,
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

type UseDashboardViewModelArgs = {
  recommended: PromptListItem[];
  starterPack: OnboardingStarterPack | null;
  missionCurrent: MissionCurrentRead | null;
  onboardingProfile: OnboardingProfile | null;
  submissions: AuthorSubmission[];
  wallet: WalletRead | null;
  billing: BillingStatus | null;
  language: Language;
  t: Translate;
};

export function useDashboardViewModel({
  recommended,
  starterPack,
  missionCurrent,
  onboardingProfile,
  submissions,
  wallet,
  billing,
  language,
  t,
}: UseDashboardViewModelArgs) {
  const localizedBillingStatus = useMemo(
    () => billingStatusLabel(billing?.status, t),
    [billing?.status, t],
  );
  const planLabel = useMemo(
    () => t(getTierTranslationKey(billing?.plan_tier ?? "free")),
    [billing?.plan_tier, t],
  );
  const highlightedPlanClassName =
    billing?.plan_tier === "enterprise" ? "text-emerald-700" : "text-zinc-900";
  const highlightedStatusClassName =
    billing?.status === "active" ? "text-emerald-700" : "text-zinc-700";

  const rejectedSubmissionsCount = useMemo(
    () => submissions.filter((submission) => submission.moderation_state === "rejected").length,
    [submissions],
  );
  const pendingSubmissionsCount = useMemo(
    () => submissions.filter((submission) => submission.moderation_state === "pending").length,
    [submissions],
  );

  const walletPendingAmount = useMemo(
    () =>
      (wallet?.pending_locked_rewards ?? [])
        .filter((reward) => reward.status === "pending")
        .reduce((sum, reward) => sum + reward.amount, 0),
    [wallet?.pending_locked_rewards],
  );

  const suggestions = useMemo<PromptListItem[]>(
    () =>
      recommended.length > 0
        ? recommended.slice(0, 2)
        : (starterPack?.prompts ?? []).slice(0, 2).map(normalizeStarterPrompt),
    [recommended, starterPack?.prompts],
  );

  const currentMission = missionCurrent?.current ?? null;
  const currentMissionView = useMemo(
    () => (currentMission ? getMissionPresentation(language, currentMission) : null),
    [currentMission, language],
  );

  const primaryAction = useMemo(() => {
    if (onboardingProfile?.needs_onboarding) {
      return {
        href: APP_ROUTES.onboarding,
        label: t("dashboard.opsContinueOnboarding"),
      };
    }

    if (currentMissionView) {
      return {
        href: currentMissionView.nextStep?.href ?? APP_ROUTES.missions,
        label: currentMissionView.nextStep?.label ?? t("dashboard.opsContinueMission"),
      };
    }

    if (starterPack?.action?.prompt_slug) {
      return {
        href: appRoute.promptBySlug(starterPack.action.prompt_slug),
        label: t("dashboard.opsContinueLearning"),
      };
    }

    return {
      href: APP_ROUTES.catalog,
      label: t("dashboard.opsOpenCatalog"),
    };
  }, [currentMissionView, onboardingProfile?.needs_onboarding, starterPack?.action?.prompt_slug, t]);

  const lessonHref = starterPack?.lesson?.slug
    ? appRoute.learnBySlug(starterPack.lesson.slug)
    : APP_ROUTES.learnStart;

  return {
    localizedBillingStatus,
    planLabel,
    highlightedPlanClassName,
    highlightedStatusClassName,
    rejectedSubmissionsCount,
    pendingSubmissionsCount,
    walletPendingAmount,
    suggestions,
    currentMissionView,
    primaryAction,
    lessonHref,
  };
}
