"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PromptCard } from "@/components/PromptCard";
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
} from "@/lib/types";

export function DashboardClient() {
  const { status } = useAuth();
  const [items, setItems] = useState<PromptListItem[] | null>(null);
  const [recommended, setRecommended] = useState<PromptListItem[]>([]);
  const [submissions, setSubmissions] = useState<AuthorSubmission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
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
        submissionsResult,
        onboardingResult,
        starterResult,
        missionResult,
      ] = await Promise.allSettled([
        fetchSavedPrompts(),
        fetchPromptRecommendations({ context: "dashboard", limit: 4 }),
        fetchBillingStatus(),
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
        setSubmissions([]);
        return;
      }

      setItems(savedResult.value);
      setRecommended(recommendedResult.status === "fulfilled" ? recommendedResult.value.items : []);
      setBilling(billingResult.value);
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

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <p className="text-sm text-zinc-600">
        {t("dashboard.signinPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("dashboard.signinLink")}
        </Link>{" "}
        {t("dashboard.signinSuffix")}
      </p>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 transition hover:border-amber-400"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (items === null) {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  const suggestions: PromptListItem[] =
    recommended.length > 0
      ? recommended.slice(0, 2)
      : (starterPack?.prompts ?? []).slice(0, 2).map(normalizeStarterPrompt);

  return (
    <div className="space-y-6">
      {searchParams.get("submitted") === "1" ? (
        <section className="rounded-[1.25rem] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {searchParams.get("autoApproved") === "1"
            ? t("dashboard.submittedAutoApproved")
            : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
        <section className="pv-panel px-5 py-5 sm:px-6">
          <p className="pv-kicker">{t("dashboard.currentMission")}</p>
          {missionCurrent?.current ? (
            <>
              <h2 className="mt-3 text-xl font-semibold tracking-[-0.03em] text-zinc-950">
                {missionCurrent.current.title}
              </h2>
              <p className="mt-2 text-sm text-zinc-600">{missionCurrent.current.objective}</p>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-200">
                <div
                  className="h-full rounded-full bg-[var(--pv-brand)]"
                  style={{
                    width: `${Math.round(
                      (missionCurrent.current.progress_count /
                        Math.max(1, missionCurrent.current.required_count)) *
                        100,
                    )}%`,
                  }}
                />
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                {missionCurrent.current.progress_count}/{missionCurrent.current.required_count}
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                {missionCurrent.current.next_step ? (
                  <Link href={missionCurrent.current.next_step.href} className="pv-button-primary">
                    {missionCurrent.current.next_step.label}
                  </Link>
                ) : null}
                <Link href="/missions" className="pv-button-secondary">
                  {t("dashboard.openMissionDetails")}
                </Link>
              </div>
            </>
          ) : (
            <>
              <h2 className="mt-3 text-xl font-semibold tracking-[-0.03em] text-zinc-950">
                {t("home.explorePrompts")}
              </h2>
              <p className="mt-2 text-sm text-zinc-600">{t("dashboard.emptyPrefix")} {t("dashboard.emptySuffix")}</p>
              <div className="mt-4">
                <Link href="/catalog" className="pv-button-primary">
                  {t("home.explorePrompts")}
                </Link>
              </div>
            </>
          )}
        </section>

        <div className="space-y-4">
          <section className="pv-panel px-5 py-5">
            <p className="pv-kicker">{t("dashboard.currentTier")}</p>
            <p className="mt-3 text-sm text-zinc-700">
              <span className="font-medium text-zinc-900">
                {t(getTierTranslationKey(billing?.plan_tier ?? "free"))}
              </span>
              {billing?.status ? ` · ${billing.status}` : ""}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
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
              </Link>
            </div>
            {billingError ? <p className="mt-2 text-sm text-red-700">{billingError}</p> : null}
          </section>

          <section className="pv-panel px-5 py-5">
            <p className="pv-kicker">{t("missions.title")}</p>
            <p className="mt-3 text-sm text-zinc-700">
              {missionCurrent?.rewards.credits ?? 0} {t("missions.credits")}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/wallet" className="pv-button-secondary">
                {t("nav.wallet")}
              </Link>
              <Link href="/store" className="pv-inline-link">
                {t("nav.store")}
              </Link>
            </div>
          </section>

          {onboardingProfile?.needs_onboarding ? (
            <section className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-medium">{t("dashboard.finishOnboardingTitle")}</p>
              <p className="mt-1">
                <Link href="/onboarding" className="underline">
                  {t("dashboard.finishOnboardingLink")}
                </Link>
              </p>
            </section>
          ) : starterPack?.action?.prompt_slug ? (
            <section className="pv-panel px-5 py-5 text-sm text-zinc-700">
              <p className="pv-kicker">{t("dashboard.recommendedNextAction")}</p>
              <p className="mt-3">{starterPack.action.instruction}</p>
              <Link
                href={`/prompt/${encodeURIComponent(starterPack.action.prompt_slug)}`}
                className="mt-4 inline-flex text-sm font-medium text-[var(--pv-brand)]"
              >
                {t("dashboard.tryNow")}
              </Link>
            </section>
          ) : null}
        </div>
      </div>

      <section className="space-y-3">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <p className="pv-kicker">{t("dashboard.savedPrompts")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              {t("dashboard.savedPrompts")}
            </h2>
          </div>
        </div>
        {items.length === 0 ? (
          <div className="rounded-[1.25rem] border border-dashed border-zinc-300 bg-zinc-50/80 p-8 text-center text-sm text-zinc-600">
            {t("dashboard.emptyPrefix")}{" "}
            <Link href="/catalog" className="font-medium text-zinc-900 underline">
              {t("dashboard.emptyLink")}
            </Link>{" "}
            {t("dashboard.emptySuffix")}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {items.map((prompt) => (
              <PromptCard key={prompt.id} prompt={prompt} />
            ))}
          </div>
        )}
      </section>

      {suggestions.length > 0 ? (
        <section className="space-y-3">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("dashboard.recommendedForYou")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {t("dashboard.recommendedForYou")}
              </h2>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {suggestions.map((prompt) => (
              <PromptCard key={`dashboard-rec-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="pv-kicker">{t("dashboard.mySubmissions")}</h2>
          <Link href="/submit" className="pv-inline-link">
            {t("dashboard.submitAnother")}
          </Link>
        </div>
        {submissions.length === 0 ? (
          <div className="rounded-[1.25rem] border border-dashed border-zinc-300 bg-zinc-50/80 p-4 text-sm text-zinc-600">
            {t("dashboard.noSubmissions")}
          </div>
        ) : (
          <div className="space-y-3">
            {submissions.slice(0, 4).map((submission) => (
              <div key={submission.id} className="pv-card p-4">
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
    return (
      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-900">
        {t("dashboard.statusApproved")}
      </span>
    );
  }
  if (state === "rejected") {
    return (
      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-900">
        {t("dashboard.statusRejected")}
      </span>
    );
  }
  if (state === "pending") {
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900">
        {t("dashboard.statusPending")}
      </span>
    );
  }
  return (
    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
      {t("dashboard.statusDraft")}
    </span>
  );
}
