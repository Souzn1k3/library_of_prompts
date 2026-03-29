"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { RouteCard } from "@/components/navigation/RouteCard";
import { PromptCard } from "@/components/PromptCard";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { ApiRequestError } from "@/lib/api";
import {
  createBillingPortalSession,
  fetchBillingStatus,
  fetchCurrentMission,
  fetchMySubmissions,
  fetchOnboardingProfile,
  fetchOnboardingStarterPack,
  fetchPromptRecommendations,
  fetchSavedPrompts,
  fetchWallet,
} from "@/lib/client-api";
import { getTierTranslationKey } from "@/lib/i18n";
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

export function DashboardClient() {
  const { status } = useAuth();
  const [items, setItems] = useState<PromptListItem[] | null>(null);
  const [recommended, setRecommended] = useState<PromptListItem[]>([]);
  const [submissions, setSubmissions] = useState<AuthorSubmission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [missionCurrent, setMissionCurrent] = useState<MissionCurrentRead | null>(null);
  const [onboardingProfile, setOnboardingProfile] = useState<OnboardingProfile | null>(null);
  const [starterPack, setStarterPack] = useState<OnboardingStarterPack | null>(null);
  const [billingError, setBillingError] = useState<string | null>(null);
  const [portalPending, setPortalPending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const searchParams = useSearchParams();
  const { t } = useI18n();

  useEffect(() => {
    if (status !== "authenticated") {
      setItems(null);
      setRecommended([]);
      setSubmissions([]);
      setError(null);
      setBilling(null);
      setWallet(null);
      setMissionCurrent(null);
      setOnboardingProfile(null);
      setStarterPack(null);
      setBillingError(null);
      return;
    }

    let cancelled = false;

    async function loadDashboard() {
      const [
        savedResult,
        recommendedResult,
        billingResult,
        walletResult,
        submissionsResult,
        onboardingResult,
        starterResult,
        missionResult,
      ] = await Promise.allSettled([
        fetchSavedPrompts(),
        fetchPromptRecommendations({ context: "dashboard", limit: 4 }),
        fetchBillingStatus(),
        fetchWallet(),
        fetchMySubmissions(),
        fetchOnboardingProfile(),
        fetchOnboardingStarterPack(),
        fetchCurrentMission(),
      ]);

      if (cancelled) return;

      const requiredFailures = [savedResult, billingResult, submissionsResult].filter(
        (result): result is PromiseRejectedResult => result.status === "rejected",
      );

      if (requiredFailures.length > 0) {
        const reason = requiredFailures[0].reason;
        if (reason instanceof ApiRequestError && reason.status === 401) {
          setItems(null);
          setRecommended([]);
          return;
        }
        setError(reason instanceof ApiRequestError ? reason.message : t("dashboard.loadError"));
        setItems([]);
        setRecommended([]);
        setBilling(null);
        setWallet(null);
        setSubmissions([]);
        return;
      }

      if (
        savedResult.status !== "fulfilled" ||
        billingResult.status !== "fulfilled" ||
        submissionsResult.status !== "fulfilled"
      ) {
        setError(t("dashboard.loadError"));
        setItems([]);
        setRecommended([]);
        setBilling(null);
        setWallet(null);
        setSubmissions([]);
        return;
      }

      setItems(savedResult.value);
      setRecommended(recommendedResult.status === "fulfilled" ? recommendedResult.value.items : []);
      setBilling(billingResult.value);
      setWallet(walletResult.status === "fulfilled" ? walletResult.value : null);
      setSubmissions(submissionsResult.value);
      setError(null);
      setBillingError(null);
      setOnboardingProfile(onboardingResult.status === "fulfilled" ? onboardingResult.value : null);
      setStarterPack(starterResult.status === "fulfilled" ? starterResult.value : null);
      setMissionCurrent(missionResult.status === "fulfilled" ? missionResult.value : null);
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [reloadToken, status, t]);

  useEffect(() => {
    if (status !== "authenticated") return;
    if (searchParams.get("billing") !== "success") return;
    let attempt = 0;
    const maxAttempts = 12;
    const interval = window.setInterval(() => {
      attempt += 1;
      fetchBillingStatus()
        .then((status) => {
          setBilling(status);
          const ready = status.status === "active" || status.status === "trialing";
          if (ready || attempt >= maxAttempts) {
            window.clearInterval(interval);
          }
        })
        .catch(() => {
          if (attempt >= maxAttempts) {
            window.clearInterval(interval);
          }
        });
    }, 2500);
    return () => window.clearInterval(interval);
  }, [searchParams, status]);

  async function openPortal() {
    setBillingError(null);
    setPortalPending(true);
    try {
      const session = await createBillingPortalSession();
      window.location.href = session.url;
    } catch (e) {
      setBillingError(e instanceof Error ? e.message : t("plans.portalFailed"));
    } finally {
      setPortalPending(false);
    }
  }

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
            onClick={() => setReloadToken((value) => value + 1)}
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
  const progressPercent = currentMission
    ? Math.round((currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100)
    : 0;
  const primaryAction = onboardingProfile?.needs_onboarding
    ? {
        href: "/onboarding",
        label: t("dashboard.finishOnboardingLink"),
      }
    : currentMission?.next_step
      ? {
          href: currentMission.next_step.href,
          label: currentMission.next_step.label,
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
  const heroTitle = onboardingProfile?.needs_onboarding
    ? t("dashboard.finishOnboardingTitle")
    : currentMission?.title ?? t("dashboard.continueWhereLeft");
  const heroDescription = onboardingProfile?.needs_onboarding
    ? t("dashboard.subtitle")
    : currentMission?.objective ??
      starterPack?.action?.instruction ??
      `${t("dashboard.emptyPrefix")} ${t("dashboard.emptySuffix")}`;
  const heroHint = onboardingProfile?.needs_onboarding
    ? t("dashboard.finishOnboardingTitle")
    : primaryAction.label
      ? `${t("dashboard.recommendedNextAction")}: ${primaryAction.label}`
      : null;
  const lessonHref = starterPack?.lesson?.slug
    ? `/learn/${encodeURIComponent(starterPack.lesson.slug)}`
    : "/learn";
  const lessonLabel = starterPack?.lesson?.title ?? t("nav.learn");
  const showOnlyPrimaryOnboardingAction = Boolean(onboardingProfile?.needs_onboarding);

  return (
    <div className="space-y-6">
      {searchParams.get("submitted") === "1" ? (
        <section className="pv-alert pv-alert-success">
          {searchParams.get("autoApproved") === "1"
            ? t("dashboard.submittedAutoApproved")
            : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <PageIntro
        eyebrow={sectionTitle}
        title={heroTitle}
        description={heroDescription}
        hint={heroHint}
        actions={
          <>
            <Link href={primaryAction.href} className="pv-button-primary">
              {primaryAction.label}
            </Link>
            {showOnlyPrimaryOnboardingAction ? null : (
              <>
                <Link href="/missions" className="pv-button-secondary">
                  {t("nav.missions")}
                </Link>
                <Link href="/catalog" className="pv-inline-link">
                  {t("home.explorePrompts")}
                  <span aria-hidden="true">↗</span>
                </Link>
              </>
            )}
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("dashboard.savedPrompts")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{items.length}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("nav.wallet")}</p>
              <div className="mt-3">
                <LmnAmount amount={wallet?.balance ?? "—"} symbol={wallet?.currency_symbol ?? "LMN"} strong />
              </div>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("dashboard.currentTier")}</p>
              <p className="mt-3 text-lg font-bold tracking-[-0.04em] text-zinc-950">
                {t(getTierTranslationKey(billing?.plan_tier ?? "free"))}
              </p>
              {billing?.status ? <p className="mt-1 text-xs text-zinc-500">{billing.status}</p> : null}
            </div>
          </div>
        }
      >
        {currentMission ? (
          <div className="space-y-4">
            <div className="pv-progress">
              <div className="pv-progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
            <div className="grid gap-3 sm:grid-cols-1">
              <div className="pv-card-muted p-4">
                <p className="pv-stat-label">{t("missions.progress")}</p>
                <p className="mt-3 text-xl font-extrabold tracking-[-0.05em] text-zinc-950">
                  {currentMission.progress_count}/{currentMission.required_count}
                </p>
              </div>
            </div>
          </div>
        ) : null}
      </PageIntro>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.85fr)]">
          <div className="min-w-0 space-y-6">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {t("dashboard.workspaceNavTitle")}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("dashboard.workspaceNavBody")}</p>
            </div>

            <EconomyLoop
              missionCard={{
                title: currentMission?.title ?? t("economy.stepEarnTitle"),
                description: currentMission?.objective ?? t("missions.subtitle"),
                href: currentMission?.next_step?.href ?? "/missions",
                actionLabel: currentMission?.next_step?.label ?? t("nav.missions"),
                badge: currentMission ? (
                  <span className="pv-chip-brand">
                    {currentMission.progress_count}/{currentMission.required_count}
                  </span>
                ) : undefined,
              }}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:h-full xl:grid-cols-1 xl:grid-rows-2">
            <RouteCard
              eyebrow={t("nav.catalog")}
              title={t("dashboard.savedPrompts")}
              description={t("catalog.subtitle")}
              href={items.length > 0 ? "/dashboard#saved" : "/catalog"}
              actionLabel={items.length > 0 ? t("dashboard.savedPrompts") : t("home.explorePrompts")}
              badge={<span className="pv-chip-brand">{items.length}</span>}
            />
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
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("dashboard.currentTier")}</h2>
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
        {billingError ? <p className="mt-3 text-sm text-red-700">{billingError}</p> : null}
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
