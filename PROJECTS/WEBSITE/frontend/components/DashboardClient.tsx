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
        } else {
          setError(reason instanceof ApiRequestError ? reason.message : t("dashboard.loadError"));
        }
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
      <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (items === null) {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  return (
    <div className="space-y-5">
      {searchParams.get("submitted") === "1" ? (
        <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {searchParams.get("autoApproved") === "1"
            ? t("dashboard.submittedAutoApproved")
            : t("dashboard.submittedPending")}
        </section>
      ) : null}

      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
        <p className="text-sm text-zinc-700">
          {t("dashboard.currentTier")}:{" "}
          <span className="font-medium text-zinc-900">
            {t(getTierTranslationKey(billing?.plan_tier ?? "free"))}
          </span>
          {billing?.status ? (
            <>
              {" "}
              · {t("dashboard.subscription")}:{" "}
              <span className="font-medium text-zinc-900">{billing.status}</span>
            </>
          ) : null}
        </p>
        {billing?.current_period_end ? (
          <p className="mt-1 text-xs text-zinc-500">
            {t("dashboard.currentPeriodEnds")}: {new Date(billing.current_period_end).toLocaleDateString()}
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={openPortal}
            disabled={portalPending}
            className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400 disabled:opacity-60"
          >
            {portalPending ? t("plans.openingCheckout") : t("dashboard.manageBilling")}
          </button>
          <Link href="/plans" className="text-sm font-medium text-zinc-900 underline">
            {t("dashboard.changePlan")}
          </Link>
        </div>
        {billingError ? <p className="mt-2 text-sm text-red-700">{billingError}</p> : null}
      </section>

      {missionCurrent?.current ? (
        <section className="space-y-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-card">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{t("dashboard.currentMission")}</p>
          <h2 className="text-lg font-semibold text-zinc-900">{missionCurrent.current.title}</h2>
          <p className="text-sm text-zinc-600">{missionCurrent.current.objective}</p>
          <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
            <div
              className="h-full rounded-full bg-zinc-900"
              style={{
                width: `${Math.round(
                  (missionCurrent.current.progress_count / Math.max(1, missionCurrent.current.required_count)) * 100,
                )}%`,
              }}
            />
          </div>
          <p className="text-xs text-zinc-500">
            {t("dashboard.continueWhereLeft")}: {missionCurrent.current.progress_count}/{missionCurrent.current.required_count}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            {missionCurrent.current.next_step ? (
              <Link
                href={missionCurrent.current.next_step.href}
                className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-800"
              >
                {missionCurrent.current.next_step.label}
              </Link>
            ) : null}
            <Link href="/missions" className="text-sm font-medium text-zinc-900 underline">
              {t("dashboard.openMissionDetails")}
            </Link>
          </div>
          {missionCurrent.latest_completed ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
              {t("dashboard.completedRewardUnlocked", { title: missionCurrent.latest_completed.title })}
            </div>
          ) : null}
          {missionCurrent.next ? (
            <p className="text-xs text-zinc-500">
              {t("dashboard.nextSuggestion", { title: missionCurrent.next.title })}
            </p>
          ) : null}
          <p className="text-xs text-zinc-500">
            {t("dashboard.rewards")}: {missionCurrent.rewards.credits} {t("missions.credits")}
            {missionCurrent.rewards.badges.length ? ` · ${missionCurrent.rewards.badges.join(", ")}` : ""}
            {missionCurrent.rewards.premium_unlock_until
              ? ` · ${t("dashboard.premiumUntil")}: ${new Date(missionCurrent.rewards.premium_unlock_until).toLocaleDateString()}`
              : ""}
          </p>
        </section>
      ) : null}

      {(recommended.length > 0 || starterPack?.prompts?.length) ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {t("dashboard.recommendedForYou")}
          </h2>
          {recommended.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {recommended.slice(0, 4).map((prompt) => (
                <PromptCard key={`dashboard-rec-${prompt.id}`} prompt={prompt} />
              ))}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {(starterPack?.prompts ?? []).slice(0, 4).map((prompt) => (
                <Link
                  key={prompt.id}
                  href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                  className="rounded-lg border border-zinc-200 bg-white p-4 shadow-card transition hover:border-zinc-300"
                >
                  <p className="text-sm font-semibold text-zinc-900">{prompt.title}</p>
                  {prompt.summary ? <p className="mt-1 text-xs text-zinc-600">{prompt.summary}</p> : null}
                </Link>
              ))}
            </div>
          )}
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          {t("dashboard.savedPrompts")}
        </h2>
        {items.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-8 text-center text-sm text-zinc-600">
            {t("dashboard.emptyPrefix")}{" "}
            <Link href="/catalog" className="font-medium text-zinc-900 underline">
              {t("dashboard.emptyLink")}
            </Link>{" "}
            {t("dashboard.emptySuffix")}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {items.map((p) => (
              <PromptCard key={p.id} prompt={p} />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{t("dashboard.mySubmissions")}</h2>
          <Link href="/submit" className="text-xs font-medium text-zinc-800 underline">
            {t("dashboard.submitAnother")}
          </Link>
        </div>
        {submissions.length === 0 ? (
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-4 text-sm text-zinc-600">
            {t("dashboard.noSubmissions")}
          </div>
        ) : (
          <div className="space-y-3">
            {submissions.slice(0, 8).map((submission) => (
              <div key={submission.id} className="rounded-lg border border-zinc-200 bg-white p-4 shadow-card">
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
                  <div className="flex flex-wrap items-center gap-2">
                    <SubmissionStateBadge state={submission.moderation_state} />
                    {submission.auto_approved ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-900">
                        {t("dashboard.autoApproved")}
                      </span>
                    ) : null}
                  </div>
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  {t("dashboard.createdAt")} {new Date(submission.created_at).toLocaleString()}
                  {submission.moderated_at
                    ? ` · ${t("dashboard.reviewedAt")} ${new Date(submission.moderated_at).toLocaleString()}`
                    : ""}
                </p>
                {submission.moderation_state !== "approved" ? (
                  <p className="mt-1 text-xs text-zinc-500">{t("dashboard.notPublicYet")}</p>
                ) : null}
                {submission.moderation_notes ? (
                  <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                    <p className="font-medium">{t("dashboard.moderationFeedback")}</p>
                    <p className="mt-1 whitespace-pre-wrap">{submission.moderation_notes}</p>
                    {submission.feedback_hints?.length ? (
                      <ul className="mt-2 space-y-1 text-amber-950">
                        {submission.feedback_hints.map((hint) => (
                          <li key={`${submission.id}-${hint}`}>• {hint}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </section>

      {onboardingProfile?.needs_onboarding ? (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-medium">{t("dashboard.finishOnboardingTitle")}</p>
          <p className="mt-1">
            {t("dashboard.finishOnboardingPrefix")}
            <Link href="/onboarding" className="underline">
              {t("dashboard.finishOnboardingLink")}
            </Link>{" "}
            {t("dashboard.finishOnboardingSuffix")}
          </p>
        </section>
      ) : null}

      {starterPack?.action?.prompt_slug ? (
        <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm text-zinc-700">
          <p className="font-medium text-zinc-900">{t("dashboard.recommendedNextAction")}</p>
          <p className="mt-1">{starterPack.action.instruction}</p>
          <Link
            href={`/prompt/${encodeURIComponent(starterPack.action.prompt_slug)}`}
            className="mt-2 inline-block font-medium text-zinc-900 underline"
          >
            {t("dashboard.tryNow")}: {starterPack.action.prompt_title}
          </Link>
        </section>
      ) : null}
    </div>
  );
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
