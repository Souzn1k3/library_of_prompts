import Link from "next/link";

import type { ScenarioExplorerSnapshot } from "@/features/scenarios/application/scenarioExplorer";
import { getTechniqueTranslationKey, type TranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type QuickFacetOption = {
  value: string;
  label: string;
};

type HomeWorkbenchSelectionPanelProps = {
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string;
  query: string;
  onQueryChange: (value: string) => void;
  onRunNow: () => void;
  runPending: boolean;
  selectedTechnique: PromptListItem["technique"] | "all";
  onSelectTechnique: (value: PromptListItem["technique"] | "all") => void;
  techniqueOptions: PromptListItem["technique"][];
  quickFacetOptions: QuickFacetOption[];
  selectedFacet: string | null;
  onToggleFacet: (value: string) => void;
  explorer: ScenarioExplorerSnapshot;
  onResetFilters: () => void;
  onSelectScenario: (slug: string) => void;
};

export function HomeWorkbenchSelectionPanel({
  t,
  query,
  onQueryChange,
  onRunNow,
  runPending,
  selectedTechnique,
  onSelectTechnique,
  techniqueOptions,
  quickFacetOptions,
  selectedFacet,
  onToggleFacet,
  explorer,
  onResetFilters,
  onSelectScenario,
}: HomeWorkbenchSelectionPanelProps) {
  return (
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
          onChange={(event) => onQueryChange(event.target.value)}
          className="pv-input"
          placeholder={t("home.entrySearchPlaceholder")}
        />
        <button type="button" onClick={onRunNow} className="pv-button-primary sm:w-auto" disabled={runPending}>
          {runPending ? t("home.entryRunPending") : t("home.entryRunNow")}
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
            {t("home.entryFilterTechnique")}
          </p>
          <div className="mt-2 pv-segmented">
            <button
              type="button"
              onClick={() => onSelectTechnique("all")}
              data-active={selectedTechnique === "all" ? "true" : "false"}
              className="pv-segment-button"
            >
              {t("home.entryFilterAll")}
            </button>
            {techniqueOptions.map((technique) => (
              <button
                key={`home-technique-${technique}`}
                type="button"
                onClick={() => onSelectTechnique(technique)}
                data-active={selectedTechnique === technique ? "true" : "false"}
                className="pv-segment-button"
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
            <div className="mt-2 pv-segmented">
              {quickFacetOptions.map((option) => (
                <button
                  key={`home-use-case-${option.value}`}
                  type="button"
                  onClick={() => onToggleFacet(option.value)}
                  data-active={selectedFacet === option.value ? "true" : "false"}
                  className="pv-segment-button"
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
              onClick={onResetFilters}
              className="pv-inline-link"
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
                  onClick={() => onSelectScenario(scenario.slug)}
                  className={`rounded-[1rem] border p-3 text-left transition ${
                    isActive
                      ? "border-[var(--pv-border-strong)] bg-[var(--pv-brand-soft)]"
                      : "border-zinc-200 bg-white hover:border-zinc-300"
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
          <div className="pv-surface-block">
            <p className="text-sm font-semibold text-zinc-900">{t("home.entryNoResultsTitle")}</p>
            <p className="mt-1 text-sm leading-relaxed text-zinc-600">{t("home.entryNoResultsBody")}</p>
            <div className="pv-action-bar pv-action-bar-start">
              <Link href="/catalog" className="pv-button-secondary !w-auto">
                {t("home.entryNoResultsAction")}
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
