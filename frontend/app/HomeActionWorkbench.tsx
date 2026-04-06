"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { HomeWorkbenchResultPanel } from "./home-workbench/HomeWorkbenchResultPanel";
import { HomeWorkbenchSelectionPanel } from "./home-workbench/HomeWorkbenchSelectionPanel";
import { useHomeWorkbenchState } from "./home-workbench/useHomeWorkbenchState";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { useScenarioDemoRun } from "@/features/scenarios/presentation/useScenarioDemoRun";
import { useScenarioEngagement } from "@/features/scenarios/presentation/useScenarioEngagement";
import { useScenarioWorkspace } from "@/features/scenarios/presentation/useScenarioWorkspace";
import { analyticsSessionId, trackEvent } from "@/lib/analytics";
import { readAttribution } from "@/lib/analytics/storage";
import { fetchGrowthRuntime } from "@/lib/client-api";
import type { PromptListItem } from "@/lib/types";

const COPY_RESET_TIMEOUT_MS = 1800;

function normalizeValue(value: string | null | undefined): string | null {
  const normalized = (value ?? "").trim().toLowerCase();
  return normalized || null;
}

function inferIntentFromCampaign(campaign: string | null): string | null {
  if (!campaign) {
    return null;
  }
  if (/(learn|course|education|exam)/.test(campaign)) {
    return "learning";
  }
  if (/(productivity|ops|workflow|automation|team)/.test(campaign)) {
    return "productivity";
  }
  if (/(growth|marketing|acquisition|revenue|ads)/.test(campaign)) {
    return "growth";
  }
  if (/(game|fun|entertain)/.test(campaign)) {
    return "entertainment";
  }
  if (/(utility|support|assistant)/.test(campaign)) {
    return "utility";
  }
  return null;
}

type HomeActionWorkbenchProps = {
  prompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export function HomeActionWorkbench({
  prompts,
  heroPromptBody,
  quickUseCases,
}: HomeActionWorkbenchProps) {
  const { t, language } = useI18n();
  const workspace = useScenarioWorkspace();
  const engagement = useScenarioEngagement();
  const [landingVariant, setLandingVariant] = useState("default");
  const [landingSource, setLandingSource] = useState<string>("direct");
  const [landingCampaign, setLandingCampaign] = useState<string | null>(null);

  const landingIntent = useMemo(() => inferIntentFromCampaign(landingCampaign), [landingCampaign]);

  const preferredFacet = useMemo(() => {
    if (landingVariant === "intent_matched" && landingIntent) {
      return landingIntent;
    }
    if (landingVariant === "source_matched") {
      const sourceFacetMap: Record<string, string> = {
        google: "productivity",
        linkedin: "productivity",
        tiktok: "growth",
        twitter: "growth",
        seo: "learning",
      };
      return sourceFacetMap[landingSource] ?? null;
    }
    return null;
  }, [landingIntent, landingSource, landingVariant]);

  const state = useHomeWorkbenchState({
    prompts,
    quickUseCases,
    heroPromptBody,
    language,
    preferredFacet,
  });

  const demoRun = useScenarioDemoRun(state.selectedPrompt?.slug ?? null);

  const [copyState, setCopyState] = useState<"idle" | "pending" | "copied" | "error">("idle");
  const [shareState, setShareState] = useState<"idle" | "copied" | "error">("idle");
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);

  const runPending = demoRun.runPending || engagement.runPending;
  const promptBySlug = useMemo(() => {
    const map = new Map<string, PromptListItem>();
    for (const prompt of prompts) {
      map.set(prompt.slug, prompt);
    }
    return map;
  }, [prompts]);

  const heroCopy = useMemo(() => {
    const base = {
      kicker: t("home.entryKicker"),
      title: t("home.entryTitle"),
      subtitle: t("home.entrySubtitle"),
    };
    if (landingVariant === "source_matched" && landingSource !== "direct") {
      return {
        kicker: `${base.kicker} · ${landingSource}`,
        title: base.title,
        subtitle: `${base.subtitle} Optimized for traffic from ${landingSource}.`,
      };
    }
    if (landingVariant === "intent_matched" && landingIntent) {
      return {
        kicker: `${base.kicker} · ${landingIntent}`,
        title: base.title,
        subtitle: `${base.subtitle} Showing scenarios aligned with "${landingIntent}" intent.`,
      };
    }
    return base;
  }, [landingIntent, landingSource, landingVariant, t]);

  useEffect(() => {
    if (copyState !== "copied") {
      return;
    }
    const timeoutId = window.setTimeout(() => setCopyState("idle"), COPY_RESET_TIMEOUT_MS);
    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  useEffect(() => {
    if (shareState !== "copied") {
      return;
    }
    const timeoutId = window.setTimeout(() => setShareState("idle"), COPY_RESET_TIMEOUT_MS);
    return () => window.clearTimeout(timeoutId);
  }, [shareState]);

  useEffect(() => {
    const attribution = readAttribution();
    const source = normalizeValue(attribution.utm_source) ?? "direct";
    const campaign = normalizeValue(attribution.utm_campaign);
    setLandingSource(source);
    setLandingCampaign(campaign);

    void fetchGrowthRuntime({
      sessionId: analyticsSessionId(),
      page: "/",
      feature: "homepage_landing",
    })
      .then((runtime) => {
        const experiment = runtime.experiments.find((item) => item.key === "landing_entry_v1");
        if (experiment?.variant) {
          setLandingVariant(experiment.variant);
        }
      })
      .catch(() => null);
  }, []);

  if (!prompts.length) {
    return (
      <section className="pv-hero px-6 py-8 sm:px-8 sm:py-10">
        <div className="space-y-4">
          <h1 className="pv-display max-w-[18ch] text-zinc-950">{t("home.entryEmptyTitle")}</h1>
          <p className="max-w-[35rem] text-sm leading-relaxed text-zinc-600">{t("home.entryEmptyBody")}</p>
          <Link href="/catalog" className="pv-button-primary w-fit">
            {t("home.entryEmptyAction")}
          </Link>
        </div>
      </section>
    );
  }

  const selectedPrompt = state.selectedPrompt;
  const isSaved = selectedPrompt ? workspace.savedSlugs.includes(selectedPrompt.slug) : false;
  const unfinishedCurrent = selectedPrompt
    ? workspace.unfinished.find((item) => item.slug === selectedPrompt.slug)
    : null;

  function selectScenarioSlug(slug: string) {
    state.selectScenarioSlug(slug);
    workspace.markRecent(slug);
  }

  async function runScenarioNow() {
    if (!selectedPrompt || !state.explorer.selectedScenario) {
      return;
    }

    const run = await demoRun.run(state.taskInput.trim() ? state.taskInput : null);
    if (!run?.executed) {
      return;
    }

    state.commitRunInput();
    workspace.markRecent(selectedPrompt.slug);
    const cleanTask = state.taskInput.trim();
    if (cleanTask) {
      workspace.saveUnfinished(selectedPrompt.slug, cleanTask);
    }
    await engagement.markScenarioRun(selectedPrompt.id);
    trackEvent({
      eventName: "scenario_run",
      page: "/",
      feature: "home_workbench",
      metadata: {
        prompt_slug: selectedPrompt.slug,
      },
    });
    setLastRunAt(new Date());
  }

  async function copyReadyScript() {
    if (!state.readyScript.trim() || !selectedPrompt) {
      return;
    }

    setCopyState("pending");
    try {
      await navigator.clipboard.writeText(state.readyScript);
      await engagement.markScenarioCopy(selectedPrompt.id);
      workspace.trackCopy(selectedPrompt.slug);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  async function shareScenario() {
    if (!selectedPrompt || typeof window === "undefined") {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/prompt/${encodeURIComponent(selectedPrompt.slug)}`,
      );
      workspace.trackShare(selectedPrompt.slug);
      setShareState("copied");
    } catch {
      setShareState("error");
    }
  }

  function toggleSaveScenario() {
    if (!selectedPrompt) {
      return;
    }
    workspace.toggleSaved(selectedPrompt.slug);
    trackEvent({
      eventName: "scenario_saved",
      page: "/",
      feature: "home_workbench",
      metadata: {
        prompt_slug: selectedPrompt.slug,
      },
    });
  }

  function resumeUnfinished(slug: string, task: string) {
    selectScenarioSlug(slug);
    state.setTaskInput(task);
    trackEvent({
      eventName: "scenario_resumed",
      page: "/",
      feature: "home_workbench",
      metadata: {
        prompt_slug: slug,
      },
    });
  }

  function markCurrentDone() {
    if (!selectedPrompt) {
      return;
    }
    workspace.clearUnfinished(selectedPrompt.slug);
    trackEvent({
      eventName: "scenario_completed",
      page: "/",
      feature: "home_workbench",
      metadata: {
        prompt_slug: selectedPrompt.slug,
      },
    });
  }

  async function purchaseBoostRuns() {
    if (!selectedPrompt) {
      return;
    }
    const purchase = await demoRun.purchaseBoost();
    if (!purchase) {
      return;
    }
    trackEvent({
      eventName: "scenario_upgrade_clicked",
      page: "/",
      feature: "home_workbench",
      metadata: {
        prompt_slug: selectedPrompt.slug,
        source: "run_boost",
        applied_bonus_runs: purchase.applied_bonus_runs,
      },
    });
  }

  return (
    <section id="home-workbench" className="pv-hero px-6 py-7 sm:px-8 sm:py-9">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] xl:items-start">
        <HomeWorkbenchSelectionPanel
          t={t}
          query={state.query}
          onQueryChange={state.setQuery}
          onRunNow={() => void runScenarioNow()}
          runPending={runPending || demoRun.capReached}
          selectedTechnique={state.selectedTechnique}
          onSelectTechnique={state.setSelectedTechnique}
          techniqueOptions={state.techniqueOptions}
          quickFacetOptions={state.quickFacetOptions}
          selectedFacet={state.selectedFacet}
          onToggleFacet={state.toggleFacet}
          explorer={state.explorer}
          onResetFilters={state.resetFilters}
          onSelectScenario={selectScenarioSlug}
          heroKicker={heroCopy.kicker}
          heroTitle={heroCopy.title}
          heroSubtitle={heroCopy.subtitle}
        />

        <HomeWorkbenchResultPanel
          t={t}
          selectedScenario={state.explorer.selectedScenario}
          selectedPrompt={selectedPrompt}
          liveResult={state.liveResult}
          taskInput={state.taskInput}
          onTaskInputChange={state.setTaskInput}
          onTaskInputBlur={(value) => {
            if (!selectedPrompt) {
              return;
            }
            const clean = value.trim();
            if (!clean) {
              workspace.clearUnfinished(selectedPrompt.slug);
              return;
            }
            workspace.saveUnfinished(selectedPrompt.slug, clean);
          }}
          hasCurrentUnfinished={Boolean(unfinishedCurrent)}
          outputDepth={state.outputDepth}
          onOutputDepthChange={state.setOutputDepth}
          onRunNow={() => void runScenarioNow()}
          runPending={runPending}
          onPurchaseBoost={() => void purchaseBoostRuns()}
          boostPending={demoRun.boostPending}
          openScenarioHref={state.openScenarioHref}
          onCopy={() => void copyReadyScript()}
          onToggleSave={toggleSaveScenario}
          onShare={() => void shareScenario()}
          copyState={copyState}
          shareState={shareState}
          isSaved={isSaved}
          engagementMessage={engagement.latestMessage}
          runGuardMessage={demoRun.latestMessage}
          lastRunAt={lastRunAt}
          demoStatus={{
            isPro: demoRun.isPro,
            remainingRuns: demoRun.remainingRuns,
            capReached: demoRun.capReached,
            bonusRunsRemaining: demoRun.bonusRunsRemaining,
          }}
          unfinished={workspace.unfinished}
          recentSlugs={workspace.recentSlugs}
          promptBySlug={promptBySlug}
          onResumeUnfinished={resumeUnfinished}
          onSelectRecent={selectScenarioSlug}
          onMarkDone={markCurrentDone}
        />
      </div>
    </section>
  );
}
