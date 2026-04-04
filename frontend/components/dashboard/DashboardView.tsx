"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { DashboardBillingSection } from "@/components/dashboard/DashboardBillingSection";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { DashboardMissionHero } from "@/components/dashboard/DashboardMissionHero";
import { DashboardSubmissionsSection } from "@/components/dashboard/DashboardSubmissionsSection";
import { DashboardWorkspaceSection } from "@/components/dashboard/DashboardWorkspaceSection";
import {
  billingStatusLabel,
  normalizeStarterPrompt,
} from "@/components/dashboard/helpers";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getTierTranslationKey, languageToIntlLocale } from "@/lib/i18n";
import { getMissionPresentation } from "@/lib/missionPresentation";
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

type DashboardViewProps = {
  status: AuthStatus;
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
  submitted: boolean;
  autoApproved: boolean;
  onReload: () => void;
};

export function DashboardView({
  status,
  items,
  recommended,
  submissions,
  error,
  billing,
  wallet,
  missionCurrent,
  onboardingProfile,
  starterPack,
  learningMy,
  learningCourse,
  submitted,
  autoApproved,
  onReload,
}: DashboardViewProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const { delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);
  const { portalError, portalPending, openPortal } = useBillingPortal();
  const sectionTitle = <span>{t("dashboard.title")}</span>;
  const localizedBillingStatus = billingStatusLabel(billing?.status, t);
  const planLabel = t(getTierTranslationKey(billing?.plan_tier ?? "free"));
  const highlightedPlan =
    billing?.plan_tier === "enterprise" ? "text-emerald-700" : "text-zinc-900";
  const highlightedStatus =
    billing?.status === "active" ? "text-emerald-700" : "text-zinc-700";
  const rejectedSubmissionsCount = submissions.filter(
    (submission) => submission.moderation_state === "rejected",
  ).length;
  const pendingSubmissionsCount = submissions.filter(
    (submission) => submission.moderation_state === "pending",
  ).length;
  const walletPendingRewards = (wallet?.pending_locked_rewards ?? []).filter(
    (reward) => reward.status === "pending",
  );
  const walletPendingAmount = walletPendingRewards.reduce((sum, reward) => sum + reward.amount, 0);

  if (status === "loading") {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={sectionTitle}
          title={t("dashboard.title")}
          description={t("dashboard.subtitle")}
        />
        <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={sectionTitle}
          title={t("dashboard.title")}
          description={t("dashboard.subtitle")}
          hint={
            <>
              {t("dashboard.signinPrefix")}{" "}
              <span className="font-semibold text-zinc-950">{t("dashboard.signinLink")}</span>{" "}
              {t("dashboard.signinSuffix")}
            </>
          }
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
              <Link href={APP_ROUTES.catalog} className="pv-inline-link">
                {t("home.explorePrompts")}
                <span aria-hidden="true">↗</span>
              </Link>
            </>
          }
        />

        <div className="pv-empty-state text-sm text-zinc-600">
          {t("dashboard.signinPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
            {t("dashboard.signinLink")}
          </Link>{" "}
          {t("dashboard.signinSuffix")}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={sectionTitle}
          title={t("dashboard.title")}
          description={t("dashboard.subtitle")}
        />

        <div className="pv-alert pv-alert-warning space-y-3">
          <p>{error}</p>
          <button
            type="button"
            onClick={onReload}
            className="pv-button-secondary !w-auto"
          >
            {t("dashboard.retry")}
          </button>
        </div>
      </div>
    );
  }

  if (items === null) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={sectionTitle}
          title={t("dashboard.title")}
          description={t("dashboard.subtitle")}
        />
        <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>
      </div>
    );
  }

  const suggestions: PromptListItem[] =
    recommended.length > 0
      ? recommended.slice(0, 2)
      : (starterPack?.prompts ?? []).slice(0, 2).map(normalizeStarterPrompt);
  const currentMission = missionCurrent?.current ?? null;
  const currentMissionView = currentMission ? getMissionPresentation(language, currentMission) : null;
  const primaryAction = onboardingProfile?.needs_onboarding
    ? {
        href: APP_ROUTES.onboarding,
        label: t("dashboard.opsContinueOnboarding"),
      }
    : currentMissionView
      ? {
          href: currentMissionView.nextStep?.href ?? APP_ROUTES.missions,
          label: currentMissionView.nextStep?.label ?? t("dashboard.opsContinueMission"),
        }
      : starterPack?.action?.prompt_slug
        ? {
          href: appRoute.promptBySlug(starterPack.action.prompt_slug),
          label: t("dashboard.opsContinueLearning"),
        }
        : {
            href: APP_ROUTES.catalog,
            label: t("dashboard.opsOpenCatalog"),
          };
  const lessonHref = starterPack?.lesson?.slug
    ? appRoute.learnBySlug(starterPack.lesson.slug)
    : APP_ROUTES.learnStart;

  return (
    <div className="space-y-6">
      {submitted ? (
        <section className="pv-alert pv-alert-success">
          {autoApproved
            ? t("dashboard.submittedAutoApproved")
            : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <DashboardMissionHero
        currentMission={currentMissionView}
        needsOnboarding={Boolean(onboardingProfile?.needs_onboarding)}
        primaryAction={primaryAction}
        learningOverviewHref={APP_ROUTES.learnMy}
        missionCompletedCount={missionCurrent?.completed_count ?? 0}
        missionTotalCount={missionCurrent?.total_count ?? 0}
        savedPromptsCount={items.length}
        submissionCount={submissions.length}
        rejectedSubmissionCount={rejectedSubmissionsCount}
        pendingSubmissionCount={pendingSubmissionsCount}
        wallet={wallet}
        balanceDelta={balanceDelta}
        learningMy={learningMy}
        learningCourse={learningCourse}
        lessonHref={lessonHref}
      />

      <DashboardWorkspaceSection
        t={t}
        locale={locale}
        savedPromptsCount={items.length}
        lastSavedPromptAt={items[0]?.created_at}
        submissionsCount={submissions.length}
        rejectedSubmissionsCount={rejectedSubmissionsCount}
        pendingSubmissionsCount={pendingSubmissionsCount}
        lastSubmissionAt={submissions[0]?.created_at}
        needsOnboarding={Boolean(onboardingProfile?.needs_onboarding)}
        learningMy={learningMy}
        wallet={wallet}
        walletPendingAmount={walletPendingAmount}
        billing={billing}
        localizedBillingStatus={localizedBillingStatus}
      />

      <DashboardBillingSection
        t={t}
        planLabel={planLabel}
        highlightedPlanClassName={highlightedPlan}
        highlightedStatusClassName={highlightedStatus}
        localizedBillingStatus={localizedBillingStatus}
        portalPending={portalPending}
        portalError={portalError}
        onOpenPortal={openPortal}
      />

      <section id="saved" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              {t("dashboard.savedPrompts")}
            </h2>
          </div>
          <span className="pv-chip-brand">{items.length}</span>
        </div>
        {items.length === 0 ? (
          <div className="pv-empty-state mt-6 text-sm text-zinc-600">
            {t("dashboard.emptyPrefix")}{" "}
            <Link href={APP_ROUTES.catalog} className="font-medium text-zinc-900 underline">
              {t("dashboard.emptyLink")}
            </Link>{" "}
            {t("dashboard.emptySuffix")}
          </div>
        ) : (
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {items.map((prompt) => (
              <PromptCard key={prompt.id} prompt={prompt} />
            ))}
          </div>
        )}
      </section>

      <DashboardSubmissionsSection t={t} locale={locale} submissions={submissions} />

      {suggestions.length > 0 || onboardingProfile?.needs_onboarding ? (
        <section
          id="recommendations"
          className="pv-panel pv-section-anchor px-6 py-6 sm:px-7"
        >
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {t("dashboard.recommendedForYou")}
              </h2>
            </div>
            <span className="pv-chip-brand">{suggestions.length + (onboardingProfile?.needs_onboarding ? 1 : 0)}</span>
          </div>
          <div className="mt-6 space-y-4">
            {onboardingProfile?.needs_onboarding ? (
              <div className="pv-alert pv-alert-warning">
                <p className="font-medium">{t("dashboard.finishOnboardingTitle")}</p>
                <p className="mt-2">
                  <Link href={APP_ROUTES.onboarding} className="underline">
                    {t("dashboard.finishOnboardingLink")}
                  </Link>
                </p>
              </div>
            ) : null}

            {suggestions.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {suggestions.map((prompt) => (
                  <PromptCard key={`dashboard-rec-${prompt.id}`} prompt={prompt} />
                ))}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}
