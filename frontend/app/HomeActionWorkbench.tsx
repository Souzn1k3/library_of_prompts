"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  buildScenarioExplorerSnapshot,
  normalizeScenarioFacet,
} from "@/features/scenarios/application/scenarioExplorer";
import { buildScenarioLiveResult } from "@/features/scenarios/application/scenarioRuntime";
import type { ScenarioResultDepth } from "@/features/scenarios/domain/scenario";
import { mapPromptListToScenarios } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import { getTechniqueTranslationKey } from "@/lib/i18n";
import {
  buildPromptFallbackTemplate,
  buildReadyScenarioScript,
  formatScenarioFacetLabel,
} from "@/lib/scenarios/text";
import type { PromptListItem } from "@/lib/types";

const COPY_RESET_TIMEOUT_MS = 1800;

type HomeActionWorkbenchProps = {
  initialAuthenticated: boolean;
  prompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export function HomeActionWorkbench({
  initialAuthenticated,
  prompts,
  heroPromptBody,
  quickUseCases,
}: HomeActionWorkbenchProps) {
  const { t, language } = useI18n();

  const [query, setQuery] = useState("");
  const [selectedTechnique, setSelectedTechnique] = useState<PromptListItem["technique"] | "all">("all");
  const [selectedFacet, setSelectedFacet] = useState<string | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(prompts[0]?.slug ?? null);
  const [taskInput, setTaskInput] = useState("");
  const [outputDepth, setOutputDepth] = useState<ScenarioResultDepth>("detailed");
  const [variationSeed, setVariationSeed] = useState(0);
  const [copyState, setCopyState] = useState<"idle" | "pending" | "copied" | "error">("idle");

  const scenarios = useMemo(() => mapPromptListToScenarios(prompts), [prompts]);

  const techniqueOptions = useMemo(
    () => [...new Set(scenarios.map((scenario) => scenario.technique))],
    [scenarios],
  );

  const quickFacetOptions = useMemo(
    () =>
      quickUseCases
        .map((facet) => ({
          value: normalizeScenarioFacet(facet),
          label: formatScenarioFacetLabel(facet),
        }))
        .filter((option): option is { value: string; label: string } => Boolean(option.value)),
    [quickUseCases],
  );

  const explorer = useMemo(
    () =>
      buildScenarioExplorerSnapshot(scenarios, {
        query,
        selectedTechnique,
        selectedFacet,
        selectedSlug,
      }),
    [query, scenarios, selectedFacet, selectedSlug, selectedTechnique],
  );

  useEffect(() => {
    if (!explorer.filteredScenarios.length) {
      return;
    }

    if (!selectedSlug || !explorer.filteredScenarios.some((scenario) => scenario.slug === selectedSlug)) {
      setSelectedSlug(explorer.filteredScenarios[0].slug);
    }
  }, [explorer.filteredScenarios, selectedSlug]);

  useEffect(() => {
    if (copyState !== "copied") {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyState("idle");
    }, COPY_RESET_TIMEOUT_MS);

    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  const selectedPrompt = useMemo(() => {
    if (!explorer.selectedScenario) {
      return null;
    }

    return prompts.find((prompt) => prompt.slug === explorer.selectedScenario?.slug) ?? null;
  }, [explorer.selectedScenario, prompts]);

  const readyScript = useMemo(() => {
    if (!selectedPrompt) {
      return "";
    }

    const selectedBody =
      heroPromptBody && prompts[0]?.slug === selectedPrompt.slug
        ? heroPromptBody
        : buildPromptFallbackTemplate(language, selectedPrompt);

    return buildReadyScenarioScript(language, selectedBody, taskInput);
  }, [heroPromptBody, language, prompts, selectedPrompt, taskInput]);

  const liveResult = useMemo(() => {
    if (!explorer.selectedScenario) {
      return "";
    }

    return buildScenarioLiveResult({
      language,
      scenario: explorer.selectedScenario,
      taskInput,
      outputDepth,
      variationSeed,
    });
  }, [explorer.selectedScenario, language, outputDepth, taskInput, variationSeed]);

  const openScenarioHref = selectedPrompt
    ? `/prompt/${encodeURIComponent(selectedPrompt.slug)}`
    : "/catalog";

  async function copyReadyScript() {
    if (!readyScript.trim()) {
      return;
    }

    setCopyState("pending");
    try {
      await navigator.clipboard.writeText(readyScript);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  function resetFilters() {
    setQuery("");
    setSelectedTechnique("all");
    setSelectedFacet(null);
  }

  function toggleFacet(facetValue: string) {
    setSelectedFacet((current) => (current === facetValue ? null : facetValue));
  }

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

  return (
    <section id="home-workbench" className="pv-hero px-6 py-7 sm:px-8 sm:py-9">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)] xl:items-start">
        <div className="space-y-5">
          <div className="max-w-[43rem] space-y-3">
            <p className="pv-kicker">{t("home.entryKicker")}</p>
            <h1 className="pv-display max-w-[22ch] text-zinc-950">{t("home.entryTitle")}</h1>
            <p className="text-sm leading-relaxed text-zinc-600">{t("home.entrySubtitle")}</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
            <label htmlFor="home-entry-search" className="sr-only">
              {t("home.entrySearchLabel")}
            </label>
            <input
              id="home-entry-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pv-input"
              placeholder={t("home.entrySearchPlaceholder")}
            />
            <Link href={openScenarioHref} className="pv-button-primary sm:w-auto">
              {t("home.entryPrimaryAction")}
            </Link>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                {t("home.entryFilterTechnique")}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedTechnique("all")}
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    selectedTechnique === "all"
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                  }`}
                >
                  {t("home.entryFilterAll")}
                </button>
                {techniqueOptions.map((technique) => (
                  <button
                    key={`home-technique-${technique}`}
                    type="button"
                    onClick={() => setSelectedTechnique(technique)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                      selectedTechnique === technique
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                    }`}
                  >
                    {t(getTechniqueTranslationKey(technique))}
                  </button>
                ))}
              </div>
            </div>

            {quickFacetOptions.length ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  {t("home.entryQuickScenarios")}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {quickFacetOptions.map((option) => (
                    <button
                      key={`home-use-case-${option.value}`}
                      type="button"
                      onClick={() => toggleFacet(option.value)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                        selectedFacet === option.value
                          ? "border-[var(--pv-brand-strong)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]"
                          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-zinc-900">
                {t("home.entryLiveResults", { count: explorer.filteredScenarios.length })}
              </p>
              {explorer.hasActiveFilters ? (
                <button
                  type="button"
                  onClick={resetFilters}
                  className="text-sm font-semibold text-zinc-500 transition hover:text-zinc-900"
                >
                  {t("home.entryResetFilters")}
                </button>
              ) : null}
            </div>

            {explorer.visibleScenarios.length ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {explorer.visibleScenarios.map((scenario) => {
                  const isActive = explorer.selectedScenario?.id === scenario.id;
                  return (
                    <button
                      key={`home-match-${scenario.id}`}
                      type="button"
                      onClick={() => setSelectedSlug(scenario.slug)}
                      className={`rounded-[1rem] border p-3 text-left transition ${
                        isActive
                          ? "border-[var(--pv-brand-strong)] bg-[var(--pv-brand-soft)] shadow-[0_8px_20px_rgba(37,92,255,0.12)]"
                          : "border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-[0_8px_18px_rgba(15,23,42,0.07)]"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="line-clamp-2 text-sm font-semibold leading-snug text-zinc-900">{scenario.title}</p>
                        <span className="rounded-full bg-white/80 px-2 py-0.5 text-[11px] font-semibold text-zinc-500">
                          {scenario.category}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-zinc-600">{scenario.summary}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
                        {scenario.qualityScore > 0 ? (
                          <span className="rounded-full bg-white/70 px-2 py-0.5">
                            {t("prompt.metricQuality", { count: scenario.qualityScore })}
                          </span>
                        ) : null}
                        {scenario.saveCount > 0 ? (
                          <span className="rounded-full bg-white/70 px-2 py-0.5">
                            {t("prompt.metricSaves", { count: scenario.saveCount })}
                          </span>
                        ) : null}
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-[1rem] border border-dashed border-zinc-300 bg-zinc-50/85 p-4">
                <p className="text-sm font-semibold text-zinc-900">{t("home.entryNoResultsTitle")}</p>
                <p className="mt-1 text-sm leading-relaxed text-zinc-600">{t("home.entryNoResultsBody")}</p>
                <Link href="/catalog" className="pv-inline-link mt-3 text-sm">
                  {t("home.entryNoResultsAction")}
                  <span aria-hidden="true">↗</span>
                </Link>
              </div>
            )}
          </div>
        </div>

        <aside className="pv-card p-5 sm:p-6">
          {explorer.selectedScenario ? (
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  {t("home.entryLiveStageKicker")}
                </p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  {explorer.selectedScenario.title}
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.entryLiveStageSubtitle")}</p>
              </div>

              <div className="space-y-2">
                <label className="pv-label" htmlFor="home-task-input">
                  {t("home.entryIntentLabel")}
                </label>
                <textarea
                  id="home-task-input"
                  value={taskInput}
                  onChange={(event) => setTaskInput(event.target.value)}
                  className="pv-textarea min-h-[98px]"
                  placeholder={t("home.entryIntentPlaceholder")}
                />
              </div>

              <div className="space-y-2">
                <p className="pv-label">{t("home.entryOutputDepthLabel")}</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setOutputDepth("detailed")}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                      outputDepth === "detailed"
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                    }`}
                  >
                    {t("home.entryOutputDepthDetailed")}
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutputDepth("concise")}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                      outputDepth === "concise"
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                    }`}
                  >
                    {t("home.entryOutputDepthConcise")}
                  </button>
                  <button
                    type="button"
                    onClick={() => setVariationSeed((current) => current + 1)}
                    className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-600 transition hover:border-zinc-300 hover:text-zinc-900"
                  >
                    {t("home.entryRefreshResult")}
                  </button>
                </div>
              </div>

              <pre className="max-h-[17.2rem] overflow-auto rounded-[0.95rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
                {liveResult}
              </pre>

              <div className="space-y-2 rounded-[1rem] border border-zinc-200 bg-zinc-50/70 p-3">
                <p className="text-sm font-semibold text-zinc-900">{t("home.entryProGateTitle")}</p>
                <p className="text-sm leading-relaxed text-zinc-600">{t("home.entryProGateBody")}</p>
                <p className="text-xs text-zinc-500">{t("home.entryProGateLimit")}</p>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <Link href={openScenarioHref} className="pv-button-primary sm:flex-1">
                  {t("home.entryPrimaryAction")}
                </Link>
                <button
                  type="button"
                  onClick={() => void copyReadyScript()}
                  disabled={copyState === "pending"}
                  className="pv-button-secondary sm:w-auto disabled:opacity-60"
                >
                  {copyState === "copied"
                    ? t("home.entryCopySuccess")
                    : copyState === "pending"
                      ? t("copy.copying")
                      : t("home.entryCopyAction")}
                </button>
              </div>

              {copyState === "error" ? <p className="text-sm text-red-700">{t("home.entryCopyError")}</p> : null}

              {copyState === "copied" ? (
                <div className="space-y-2 rounded-[1rem] border border-emerald-200 bg-emerald-50/80 p-3">
                  <p className="text-sm leading-relaxed text-emerald-900">{t("home.entryCopiedHint")}</p>
                  <div className="flex flex-wrap gap-2">
                    <Link href={openScenarioHref} className="rounded-full border border-emerald-300 px-3 py-1.5 text-xs font-semibold text-emerald-900 transition hover:bg-emerald-100">
                      {t("home.entryNextActionOpen")}
                    </Link>
                    <Link
                      href={initialAuthenticated ? "/dashboard" : "/signup"}
                      className="rounded-full border border-emerald-300 px-3 py-1.5 text-xs font-semibold text-emerald-900 transition hover:bg-emerald-100"
                    >
                      {t(initialAuthenticated ? "home.entryNextActionSaveAuth" : "home.entryNextActionSaveGuest")}
                    </Link>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}
