"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { DashboardMissionHero } from "@/components/dashboard/DashboardMissionHero";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { RouteCard } from "@/components/navigation/RouteCard";
import { PromptCard } from "@/components/PromptCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatDateTime } from "@/lib/formatters";
import { getTierTranslationKey, languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import { getMissionPresentation } from "@/lib/missionPresentation";
import type {
  AuthorSubmission,
  BillingStatus,
  MissionCurrentRead,
  OnboardingProfile,
  OnboardingStarterPack,
  PromptListItem,
  PromptTechnique,
  WalletRead,
} from "@/lib/types";

function billingStatusLabel(
  status: string | null | undefined,
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string,
): string | null {
  if (!status) {
    return null;
  }
  const key = `plans.billingStatus.${status}` as TranslationKey;
  const translated = t(key);
  return translated === key ? t("plans.billingStatus.unknown") : translated;
}

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
        label: t("dashboard.finishOnboardingLink"),
      }
    : currentMissionView
      ? {
          href: currentMissionView.nextStep?.href ?? APP_ROUTES.missions,
          label: t("dashboard.openCurrentTask"),
        }
      : starterPack?.action?.prompt_slug
        ? {
            href: appRoute.promptBySlug(starterPack.action.prompt_slug),
            label: t("dashboard.tryNow"),
          }
        : {
            href: APP_ROUTES.catalog,
            label: t("home.explorePrompts"),
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
        savedPromptsCount={items.length}
        savedPromptsPreviewTitle={items[0]?.title ?? null}
        submissionCount={submissions.length}
        latestSubmissionTitle={submissions[0]?.title ?? null}
        wallet={wallet}
        balanceDelta={balanceDelta}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("dashboard.workspaceNavTitle")}
          </h2>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div>
            <RouteCard
              eyebrow={t("nav.store")}
              title={t("economy.stepSpendTitle")}
              description={t("store.subtitle")}
              href={APP_ROUTES.store}
              actionLabel={t("nav.store")}
              tone="spend"
            />
          </div>

          <div>
            <RouteCard
              eyebrow={t("nav.learn")}
              title={t("dashboard.mapLearningTitle")}
              description={t("dashboard.mapLearningBody")}
              href={lessonHref}
              actionLabel={t("dashboard.mapLearningAction")}
            />
          </div>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("nav.billing")}</h2>
            <p className="mt-2 text-sm text-zinc-600">{t("dashboard.billingBody")}</p>
          </div>
          <span className={`pv-chip-brand ${highlightedPlan}`}>{planLabel}</span>
        </div>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="pv-card-muted p-4">
            <p className="pv-kicker">{t("plans.currentTier")}</p>
            <p className={`mt-2 text-base font-semibold ${highlightedPlan}`}>{planLabel}</p>
          </div>
          <div className="pv-card-muted p-4">
            <p className="pv-kicker">{t("plans.subscriptionStatus")}</p>
            <p className={`mt-2 text-base font-semibold ${highlightedStatus}`}>
              {localizedBillingStatus ?? t("plans.billingStatus.unknown")}
            </p>
          </div>
          <div className="pv-card-muted p-4">
            <p className="pv-kicker">{t("dashboard.manageBilling")}</p>
            <p className="mt-2 text-sm text-zinc-700">{t("dashboard.billingActionHint")}</p>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={openPortal}
            disabled={portalPending}
            className="pv-button-secondary disabled:opacity-60"
          >
            {portalPending ? t("plans.openingCheckout") : t("dashboard.manageBilling")}
          </button>
          <Link href={APP_ROUTES.pricing} className="pv-button-primary">
            {t("dashboard.changePlan")}
          </Link>
        </div>
        {portalError ? <p className="mt-3 text-sm text-red-700">{portalError}</p> : null}
      </section>

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

      <section id="submissions" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("dashboard.mySubmissions")}</h2>
          </div>
          <Link href={APP_ROUTES.submit} className="pv-inline-link">
            {t("dashboard.submitAnother")}
            <span aria-hidden="true">↗</span>
          </Link>
        </div>
        {submissions.length === 0 ? (
          <div className="pv-empty-state mt-6 text-sm text-zinc-600">{t("dashboard.noSubmissions")}</div>
        ) : (
          <div className="mt-6 space-y-3">
            {submissions.slice(0, 4).map((submission) => (
              <div key={submission.id} className="pv-card-muted p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  {submission.moderation_state === "approved" ? (
                    <Link
                      href={appRoute.promptBySlug(submission.slug)}
                      className="text-sm font-semibold text-zinc-900 underline"
                    >
                      {submission.title}
                    </Link>
                  ) : (
                    <p className="text-sm font-semibold text-zinc-900">{submission.title}</p>
                  )}
                  <SubmissionStateBadge state={submission.moderation_state} />
                </div>
                <p className="mt-2 text-xs text-zinc-500">
                  {t("dashboard.createdAt")} {formatDateTime(submission.created_at, locale)}
                </p>
                {submission.moderation_notes ? (
                  <p className="mt-2 text-sm text-zinc-600">{submission.moderation_notes}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

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

function normalizeStarterPrompt(prompt: OnboardingStarterPack["prompts"][number]): PromptListItem {
  return {
    id: prompt.id,
    slug: prompt.slug,
    title: prompt.title,
    summary: prompt.summary,
    technique: (prompt.technique as PromptTechnique) ?? "other",
    category_id: prompt.category_id,
    status: "published",
    moderation_state: "approved",
    author_id: null,
    created_at: new Date(0).toISOString(),
  };
}

function SubmissionStateBadge({
  state,
}: {
  state: AuthorSubmission["moderation_state"];
}) {
  const { t } = useI18n();
  if (state === "approved") {
    return <span className="pv-badge-success">{t("dashboard.statusApproved")}</span>;
  }
  if (state === "rejected") {
    return <span className="pv-badge-danger">{t("dashboard.statusRejected")}</span>;
  }
  if (state === "pending") {
    return <span className="pv-badge-warning">{t("dashboard.statusPending")}</span>;
  }
  return <span className="pv-badge">{t("dashboard.statusDraft")}</span>;
}
