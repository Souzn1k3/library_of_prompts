"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { PromptCard } from "@/components/PromptCard";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import {
  fetchMySubmissions,
  fetchPromptRecommendations,
  fetchScenarioWorkspace,
} from "@/lib/client-api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { languageToIntlLocale } from "@/lib/i18n";
import type {
  AuthorSubmission,
  PromptListItem,
  ScenarioWorkspaceRead,
} from "@/lib/types";

type WorkspaceState = {
  loading: boolean;
  error: string | null;
  workspace: ScenarioWorkspaceRead | null;
  recommended: PromptListItem[];
  submissions: AuthorSubmission[];
};

const INITIAL_STATE: WorkspaceState = {
  loading: false,
  error: null,
  workspace: null,
  recommended: [],
  submissions: [],
};

export function WorkspaceDashboardClient() {
  const { status, user } = useAuth();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const [state, setState] = useState<WorkspaceState>(INITIAL_STATE);

  useEffect(() => {
    if (status !== "authenticated") {
      setState(INITIAL_STATE);
      return;
    }

    let cancelled = false;
    setState((current) => ({
      ...current,
      loading: true,
      error: null,
    }));

    async function loadWorkspace() {
      const [workspaceResult, recommendedResult, submissionsResult] = await Promise.allSettled([
        fetchScenarioWorkspace({ recent_limit: 6, saved_limit: 8, unfinished_limit: 6 }),
        fetchPromptRecommendations({ context: "dashboard", limit: 4 }),
        fetchMySubmissions(),
      ]);

      if (cancelled) {
        return;
      }

      if (workspaceResult.status === "rejected") {
        setState({
          loading: false,
          error: getErrorMessage(workspaceResult.reason, t("dashboard.loadError")),
          workspace: null,
          recommended: [],
          submissions: [],
        });
        return;
      }

      setState({
        loading: false,
        error: null,
        workspace: workspaceResult.value,
        recommended: recommendedResult.status === "fulfilled" ? recommendedResult.value.items : [],
        submissions: submissionsResult.status === "fulfilled" ? submissionsResult.value : [],
      });
    }

    void loadWorkspace();

    return () => {
      cancelled = true;
    };
  }, [status, t]);

  if (status === "loading") {
    return <WorkspaceLoadingView title={t("dashboard.title")} subtitle={t("dashboard.loading")} />;
  }

  if (status === "unauthenticated") {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.dashboard")}
          title={t("dashboard.title")}
          description={t("dashboard.subtitle")}
          showDescription
          actions={(
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary !w-auto">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-secondary !w-auto">
                {t("nav.signup")}
              </Link>
              <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
                {t("dashboard.opsOpenCatalog")}
              </Link>
            </>
          )}
        />

        <section className="pv-panel px-6 py-6 sm:px-7">
          <p className="text-sm leading-relaxed text-zinc-600">
            {t("dashboard.signinPrefix")} <Link href={APP_ROUTES.login} className="pv-inline-link">{t("dashboard.signinLink")}</Link>{" "}
            {t("dashboard.signinSuffix")}
          </p>
        </section>
      </div>
    );
  }

  const unfinished = state.workspace?.unfinished ?? [];
  const savedPrompts = dedupePrompts((state.workspace?.saved ?? []).map((item) => item.prompt));
  const recentItems = state.workspace?.recent ?? [];
  const savedDescription = savedPrompts.length
    ? t("home.pathLibraryBodyAuth")
    : `${t("dashboard.emptyPrefix")} ${t("dashboard.emptyLink")} ${t("dashboard.emptySuffix")}`;

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.dashboard")}
        title={user?.display_name ? `${t("dashboard.title")} · ${user.display_name}` : t("dashboard.title")}
        description={t("dashboard.subtitle")}
        showDescription
        actions={(
          <>
            <Link href={APP_ROUTES.catalog} className="pv-button-primary !w-auto">
              {t("dashboard.opsOpenCatalog")}
            </Link>
            <Link href={APP_ROUTES.submit} className="pv-button-secondary !w-auto">
              {t("dashboard.submitAnother")}
            </Link>
          </>
        )}
        aside={(
          <div className="pv-card p-5">
            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <WorkspaceCount label={t("home.entryUnfinishedTitle")} value={unfinished.length} />
              <WorkspaceCount label={t("dashboard.savedPrompts")} value={savedPrompts.length} />
              <WorkspaceCount label={t("home.entryRecentTitle")} value={recentItems.length} />
            </div>
          </div>
        )}
      />

      {state.loading && !state.workspace ? <WorkspaceLoadingView subtitle={t("dashboard.loading")} /> : null}

      {state.error ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <p className="text-sm text-red-700">{state.error}</p>
        </section>
      ) : null}

      {unfinished.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("home.entryUnfinishedTitle")} description={t("home.entryUnfinishedHint")} />
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {unfinished.map((item) => (
              <article key={`unfinished-${item.prompt.id}`} className="pv-card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{item.prompt.title}</h2>
                    <p className="mt-2 line-clamp-4 text-sm leading-relaxed text-zinc-600">{item.unfinished_task}</p>
                  </div>
                  <span className="pv-chip-brand whitespace-nowrap">{formatDate(item.last_used_at, locale)}</span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link href={appRoute.promptBySlug(item.prompt.slug)} className="pv-button-primary !w-auto">
                    {t("home.entryUnfinishedResume")}
                  </Link>
                  <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
                    {t("dashboard.opsOpenCatalog")}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {savedPrompts.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("dashboard.savedPrompts")} description={savedDescription} />
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {savedPrompts.map((prompt) => (
              <PromptCard key={`workspace-saved-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("dashboard.savedPrompts")} description={savedDescription} />
          <div className="mt-4">
            <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
              {t("dashboard.opsOpenCatalog")}
            </Link>
          </div>
        </section>
      )}

      {recentItems.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("home.entryRecentTitle")} description={t("dashboard.workspaceNavBody")} />
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {recentItems.map((item) => (
              <Link
                key={`recent-${item.prompt.id}`}
                href={appRoute.promptBySlug(item.prompt.slug)}
                className="pv-card block p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{item.prompt.title}</h2>
                    <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-zinc-600">
                      {item.prompt.summary || t("prompt.noSummary")}
                    </p>
                  </div>
                  <span className="pv-chip whitespace-nowrap">{formatDate(item.last_used_at, locale)}</span>
                </div>
                <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
                  {t("prompt.openPrompt")}
                  <span aria-hidden="true">↗</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {state.recommended.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("dashboard.recommendedForYou")} description={t("home.pathPractitionerBody")} />
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {state.recommended.map((prompt) => (
              <PromptCard key={`workspace-recommendation-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {state.submissions.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionHeading title={t("dashboard.mySubmissions")} description={t("dashboard.submitAnother")} />
          <div className="mt-5 grid gap-3 lg:grid-cols-2">
            {state.submissions.slice(0, 6).map((submission) => (
              <article key={`submission-${submission.id}`} className="pv-card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{submission.title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-zinc-600">
                      {formatSubmissionStatus(submission.moderation_state, t)}
                    </p>
                  </div>
                  <span className="pv-chip whitespace-nowrap">{formatDate(submission.created_at, locale)}</span>
                </div>
                <div className="mt-4">
                  <Link href={APP_ROUTES.submit} className="pv-button-secondary !w-auto">
                    {t("dashboard.submitAnother")}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function WorkspaceLoadingView({ title, subtitle }: { title?: string; subtitle: string }) {
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      {title ? <h1 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h1> : null}
      <p className={`${title ? "mt-2" : ""} text-sm text-zinc-500`}>{subtitle}</p>
    </section>
  );
}

function SectionHeading({ title, description }: { title: string; description: string }) {
  return (
    <div className="max-w-[46rem]">
      <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">{description}</p>
    </div>
  );
}

function WorkspaceCount({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[1rem] border border-[var(--pv-border)] bg-zinc-50/80 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{value}</p>
    </div>
  );
}

function dedupePrompts(prompts: PromptListItem[]) {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}

function formatDate(value: string | null | undefined, locale: string) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "short",
  }).format(date);
}

function formatSubmissionStatus(
  status: AuthorSubmission["moderation_state"],
  t: (key: string, params?: Record<string, string | number | null | undefined>) => string,
) {
  if (status === "approved") {
    return t("dashboard.statusApproved");
  }
  if (status === "rejected") {
    return t("dashboard.statusRejected");
  }
  if (status === "pending") {
    return t("dashboard.statusPending");
  }
  return t("dashboard.statusDraft");
}
