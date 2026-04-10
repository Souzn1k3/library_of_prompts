"use client";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { DashboardBillingSection } from "@/components/dashboard/DashboardBillingSection";
import { DashboardMissionHero } from "@/components/dashboard/DashboardMissionHero";
import { DashboardRecommendationsSection } from "@/components/dashboard/DashboardRecommendationsSection";
import { DashboardSavedPromptsSection } from "@/components/dashboard/DashboardSavedPromptsSection";
import {
  DashboardErrorView,
  DashboardLoadingView,
  DashboardUnauthenticatedView,
} from "@/components/dashboard/DashboardStatusViews";
import { DashboardSubmissionsSection } from "@/components/dashboard/DashboardSubmissionsSection";
import { DashboardWorkspaceSection } from "@/components/dashboard/DashboardWorkspaceSection";
import { useDashboardViewModel } from "@/components/dashboard/useDashboardViewModel";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { APP_ROUTES } from "@/lib/constants/routes";
import { languageToIntlLocale } from "@/lib/i18n";
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
  const needsOnboarding = Boolean(onboardingProfile?.needs_onboarding);
  const sectionTitle = <span>{t("dashboard.title")}</span>;

  const {
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
  } = useDashboardViewModel({
    recommended,
    starterPack,
    missionCurrent,
    onboardingProfile,
    submissions,
    wallet,
    billing,
    language,
    t,
  });

  if (status === "loading") {
    return <DashboardLoadingView t={t} sectionTitle={sectionTitle} />;
  }

  if (status === "unauthenticated") {
    return <DashboardUnauthenticatedView t={t} sectionTitle={sectionTitle} />;
  }

  if (error) {
    return <DashboardErrorView t={t} sectionTitle={sectionTitle} error={error} onReload={onReload} />;
  }

  if (items === null) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={sectionTitle}
          title={t("dashboard.title")}
          titleClassName="text-2xl font-bold tracking-[-0.04em] sm:text-2xl"
          description={t("dashboard.subtitle")}
        />
        <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {submitted ? (
        <section className="pv-alert pv-alert-success">
          {autoApproved ? t("dashboard.submittedAutoApproved") : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <DashboardMissionHero
        currentMission={currentMissionView}
        needsOnboarding={needsOnboarding}
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
        needsOnboarding={needsOnboarding}
        learningMy={learningMy}
        wallet={wallet}
        walletPendingAmount={walletPendingAmount}
        billing={billing}
        localizedBillingStatus={localizedBillingStatus}
      />

      <DashboardBillingSection
        t={t}
        planLabel={planLabel}
        highlightedPlanClassName={highlightedPlanClassName}
        highlightedStatusClassName={highlightedStatusClassName}
        localizedBillingStatus={localizedBillingStatus}
        portalPending={portalPending}
        portalError={portalError}
        onOpenPortal={openPortal}
      />

      <DashboardSavedPromptsSection items={items} t={t} />
      <DashboardSubmissionsSection t={t} locale={locale} submissions={submissions} />
      <DashboardRecommendationsSection suggestions={suggestions} needsOnboarding={needsOnboarding} t={t} />
    </div>
  );
}
