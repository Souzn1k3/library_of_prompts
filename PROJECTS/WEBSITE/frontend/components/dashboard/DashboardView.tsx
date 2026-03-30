"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { DashboardMissionHero } from "@/components/dashboard/DashboardMissionHero";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { RouteCard } from "@/components/navigation/RouteCard";
import { PromptCard } from "@/components/PromptCard";
import { LmnMark } from "@/components/ui/LmnMark";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { getTierTranslationKey } from "@/lib/i18n";
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
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);
  const { portalError, portalPending, openPortal } = useBillingPortal();
  const sectionTitle = <span>{t("dashboard.title")}</span>;

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
              <Link href="/login" className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href="/signup" className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
              <Link href="/catalog" className="pv-inline-link">
                {t("home.explorePrompts")}
                <span aria-hidden="true">↗</span>
              </Link>
            </>
          }
        />

        <div className="pv-empty-state text-sm text-zinc-600">
          {t("dashboard.signinPrefix")}{" "}
          <Link href="/login" className="font-medium text-zinc-900 underline">
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
        href: "/onboarding",
        label: t("dashboard.finishOnboardingLink"),
      }
    : currentMissionView?.nextStep
      ? {
          href: currentMissionView.nextStep.href,
          label: t("learn.continueMission"),
        }
      : starterPack?.action?.prompt_slug
        ? {
            href: `/prompt/${encodeURIComponent(starterPack.action.prompt_slug)}`,
            label: t("dashboard.tryNow"),
          }
        : {
            href: "/catalog",
            label: t("home.explorePrompts"),
          };
  const secondaryAction = onboardingProfile?.needs_onboarding
    ? null
    : primaryAction.href === "/missions"
      ? { href: "/catalog", label: t("home.explorePrompts") }
      : { href: "/missions", label: t("nav.missions") };
  const lessonHref = starterPack?.lesson?.slug
    ? `/learn/${encodeURIComponent(starterPack.lesson.slug)}`
    : "/learn";
  const lessonLabel = starterPack?.lesson?.title ?? t("nav.learn");

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
        secondaryAction={secondaryAction}
        savedPromptsCount={items.length}
        savedPromptsPreviewTitle={items[0]?.title ?? null}
        submissionCount={submissions.length}
        latestSubmissionTitle={submissions[0]?.title ?? null}
        wallet={wallet}
        balanceDelta={balanceDelta}
        balanceChange={balanceChange}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("dashboard.workspaceNavTitle")}
          </h2>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-12">
          <div className="xl:col-span-4">
            <RouteCard
              eyebrow={t("nav.missions")}
              title={currentMissionView?.title ?? t("economy.stepEarnTitle")}
              description={currentMissionView?.objective ?? t("missions.subtitle")}
              href={currentMissionView?.nextStep?.href ?? "/missions"}
              actionLabel={currentMissionView?.nextStep?.label ?? t("nav.missions")}
              badge={
                currentMissionView ? (
                  <span className="pv-chip-brand">
                    {currentMissionView.mission.progress_count}/{currentMissionView.mission.required_count}
                  </span>
                ) : undefined
              }
              tone="earn"
              visual={<LmnMark size={30} tone="earned" />}
            />
          </div>

          <div className="xl:col-span-4">
            <RouteCard
              eyebrow={t("nav.wallet")}
              title={t("economy.stepBalanceTitle")}
              description={t("wallet.subtitle")}
              href="/wallet"
              actionLabel={t("nav.wallet")}
              tone="balance"
              visual={<LmnMark size={30} tone="balance" />}
            />
          </div>

          <div className="xl:col-span-4">
            <RouteCard
              eyebrow={t("nav.store")}
              title={t("economy.stepSpendTitle")}
              description={t("store.subtitle")}
              href="/store"
              actionLabel={t("nav.store")}
              tone="spend"
              visual={<LmnMark size={30} tone="spent" />}
            />
          </div>

          <div className="xl:col-span-6">
            <RouteCard
              eyebrow={t("nav.catalog")}
              title={t("dashboard.savedPrompts")}
              description={t("catalog.subtitle")}
              href={items.length > 0 ? "/dashboard#saved" : "/catalog"}
              actionLabel={items.length > 0 ? t("dashboard.savedPrompts") : t("home.explorePrompts")}
              badge={<span className="pv-chip-brand">{items.length}</span>}
            />
          </div>

          <div className="xl:col-span-6">
            <RouteCard
              eyebrow={t("nav.learn")}
              title={lessonLabel}
              description={starterPack?.lesson ? t("dashboard.recommendedNextAction") : t("learn.subtitle")}
              href={lessonHref}
              actionLabel={starterPack?.lesson ? t("home.startLearning") : t("nav.learn")}
            />
          </div>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("nav.billing")}</h2>
          </div>
          <span className="pv-chip-brand">{t(getTierTranslationKey(billing?.plan_tier ?? "free"))}</span>
        </div>
        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2 text-sm text-zinc-700">
            <p>
              <span className="font-medium text-zinc-900">{t(getTierTranslationKey(billing?.plan_tier ?? "free"))}</span>
              {billing?.status ? ` · ${billing.status}` : ""}
            </p>
            <p className="text-zinc-600">{t("dashboard.changePlan")}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={openPortal}
              disabled={portalPending}
              className="pv-button-secondary disabled:opacity-60"
            >
              {portalPending ? t("plans.openingCheckout") : t("dashboard.manageBilling")}
            </button>
            <Link href="/pricing" className="pv-inline-link">
              {t("dashboard.changePlan")}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
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
            <Link href="/catalog" className="font-medium text-zinc-900 underline">
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
                  <Link href="/onboarding" className="underline">
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

      <section id="submissions" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("dashboard.mySubmissions")}</h2>
          </div>
          <Link href="/submit" className="pv-inline-link">
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
                      href={`/prompt/${encodeURIComponent(submission.slug)}`}
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
                  {t("dashboard.createdAt")} {new Date(submission.created_at).toLocaleString()}
                </p>
                {submission.moderation_notes ? (
                  <p className="mt-2 text-sm text-zinc-600">{submission.moderation_notes}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>
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
