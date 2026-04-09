"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import {
  DashboardErrorView,
  DashboardLoadingView,
  DashboardUnauthenticatedView,
} from "@/components/dashboard/DashboardStatusViews";
import { useDashboardViewModel } from "@/components/dashboard/useDashboardViewModel";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
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

function formatShortDate(value: string | null | undefined, locale: string) {
  if (!value) {
    return null;
  }

  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

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
  const needsOnboarding = Boolean(onboardingProfile?.needs_onboarding);
  const sectionTitle = <span>{t("dashboard.title")}</span>;

  const {
    localizedBillingStatus,
    planLabel,
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
    return <DashboardLoadingView t={t} sectionTitle={sectionTitle} />;
  }

  const activeCourse = learningMy?.active_courses[0] ?? null;
  const latestSubmission = submissions[0] ?? null;
  const lastSavedPrompt = items[0] ?? null;
  const missionProgress = currentMissionView
    ? Math.round((currentMissionView.mission.progress_count / Math.max(1, currentMissionView.mission.required_count)) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {submitted ? (
        <section className="pv-alert pv-alert-success">
          {autoApproved ? t("dashboard.submittedAutoApproved") : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.22fr)_minmax(18rem,0.78fr)] xl:items-start">
          <div className="space-y-5">
            <div className="space-y-3">
              <p className="pv-kicker">{t("dashboard.title")}</p>
              <h1 className="text-4xl font-semibold tracking-[-0.06em] text-zinc-950 sm:text-5xl">
                {needsOnboarding
                  ? t("dashboard.finishOnboardingTitle")
                  : currentMissionView?.title ?? t("dashboard.title")}
              </h1>
              <p className="pv-lead">
                {needsOnboarding
                  ? t("dashboard.subtitle")
                  : currentMissionView?.objective ?? t("dashboard.subtitle")}
              </p>
            </div>

            <div className="pv-cta-group">
              <Link href={primaryAction.href} className="pv-button-primary !w-auto">
                {primaryAction.label}
              </Link>
              <Link href={lessonHref} className="pv-button-secondary !w-auto">
                {activeCourse ? t("learn.continue") : t("home.startLearning")}
              </Link>
            </div>
          </div>

          <div className="grid gap-3">
            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("missions.progress")}
              </p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-zinc-950">
                {currentMissionView
                  ? `${currentMissionView.mission.progress_count}/${currentMissionView.mission.required_count}`
                  : "0/0"}
              </p>
              <p className="mt-2 text-sm text-zinc-600">
                {currentMissionView ? `${missionProgress}%` : t("missions.subtitle")}
              </p>
            </div>

            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("learn.title")}
              </p>
              <p className="mt-2 text-lg font-semibold tracking-[-0.04em] text-zinc-950">
                {activeCourse?.title ?? learningCourse?.title ?? t("learn.title")}
              </p>
              <p className="mt-2 text-sm text-zinc-600">
                {activeCourse ? `${activeCourse.progress_percent}%` : t("learn.catalogPathHint")}
              </p>
            </div>

            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("plans.currentTier")}
              </p>
              <p className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">{planLabel}</p>
              <p className="mt-2 text-sm text-zinc-600">
                {localizedBillingStatus ?? `${wallet?.balance ?? 0} ${wallet?.currency_symbol ?? ""}`}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <article className="pv-card flex h-full flex-col p-5">
          <p className="pv-kicker">{t("nav.catalog")}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
            {items.length.toLocaleString(locale)}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            {lastSavedPrompt
              ? `${lastSavedPrompt.title} · ${formatShortDate(lastSavedPrompt.created_at, locale)}`
              : t("dashboard.loading")}
          </p>
          <div className="mt-auto pt-5">
            <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
              {t("home.explorePrompts")}
            </Link>
          </div>
        </article>

        <article className="pv-card flex h-full flex-col p-5">
          <p className="pv-kicker">{t("learn.title")}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
            {learningCourse?.title ?? activeCourse?.title ?? t("learn.title")}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            {learningCourse?.description ?? activeCourse?.subtitle ?? t("learn.releaseSubtitle")}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
            {learningCourse ? <span className="pv-chip">{learningCourse.progress_percent}%</span> : null}
            {starterPack?.lesson ? <span className="pv-chip-brand">{starterPack.lesson.title}</span> : null}
          </div>
          <div className="mt-auto pt-5">
            <Link href={lessonHref} className="pv-button-secondary !w-auto">
              {activeCourse ? t("learn.continue") : t("home.startLearning")}
            </Link>
          </div>
        </article>

        <article className="pv-card flex h-full flex-col p-5">
          <p className="pv-kicker">{t("footer.account")}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
            {wallet?.balance ?? 0}
            {wallet?.currency_symbol ? ` ${wallet.currency_symbol}` : ""}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            {balanceDelta
              ? `${balanceDelta > 0 ? "+" : ""}${balanceDelta}`
              : localizedBillingStatus ?? t("plans.currentTier")}
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-500">
            <span className="pv-chip">{submissions.length} {t("nav.missions").toLowerCase()}</span>
            {walletPendingAmount > 0 ? <span className="pv-chip-brand">+{walletPendingAmount}</span> : null}
          </div>
          <div className="mt-auto pt-5">
            <Link href={APP_ROUTES.pricing} className="pv-button-secondary !w-auto">
              {t("plans.manageBilling")}
            </Link>
          </div>
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("dashboard.title")}</p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">
                {t("dashboard.recommendedForYou")}
              </h2>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            {suggestions.map((prompt) => (
              <Link
                key={prompt.id}
                href={appRoute.promptBySlug(prompt.slug)}
                className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 px-4 py-4 transition hover:border-[var(--pv-border-strong)]"
              >
                <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{prompt.title}</p>
                {prompt.summary ? (
                  <p className="mt-2 text-sm leading-relaxed text-zinc-600">{prompt.summary}</p>
                ) : null}
              </Link>
            ))}
          </div>
        </section>

        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("nav.profile")}</p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">
                {t("nav.dashboard")}
              </h2>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 px-4 py-4">
              <p className="text-sm font-semibold text-zinc-950">{currentMissionView?.title ?? t("nav.missions")}</p>
              <p className="mt-1 text-sm text-zinc-600">
                {currentMissionView?.completionCondition ?? t("missions.subtitle")}
              </p>
            </div>
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 px-4 py-4">
              <p className="text-sm font-semibold text-zinc-950">
                {latestSubmission?.title ?? t("submit.pageTitle")}
              </p>
              <p className="mt-1 text-sm text-zinc-600">
                {latestSubmission
                  ? `${latestSubmission.moderation_state} · ${formatShortDate(latestSubmission.created_at, locale)}`
                  : `${pendingSubmissionsCount + rejectedSubmissionsCount} / ${submissions.length}`}
              </p>
            </div>
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 px-4 py-4">
              <p className="text-sm font-semibold text-zinc-950">{t("plans.currentTier")}</p>
              <p className="mt-1 text-sm text-zinc-600">
                {planLabel}
                {localizedBillingStatus ? ` · ${localizedBillingStatus}` : ""}
              </p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <Link href={APP_ROUTES.missions} className="pv-button-primary !w-auto">
              {t("nav.missions")}
            </Link>
            <Link href={APP_ROUTES.submit} className="pv-button-secondary !w-auto">
              {t("submit.pageTitle")}
            </Link>
          </div>
        </section>
      </section>
    </div>
  );
}
