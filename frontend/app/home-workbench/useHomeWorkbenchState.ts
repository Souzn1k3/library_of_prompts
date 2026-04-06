"use client";

import { useEffect, useMemo, useState } from "react";

import {
  buildScenarioExplorerSnapshot,
  normalizeScenarioFacet,
  type ScenarioExplorerSnapshot,
} from "@/features/scenarios/application/scenarioExplorer";
import { buildScenarioLiveResult } from "@/features/scenarios/application/scenarioRuntime";
import type { ScenarioResultDepth } from "@/features/scenarios/domain/scenario";
import { mapPromptListToScenarios } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import type { Language } from "@/lib/i18n";
import { buildPromptFallbackTemplate, buildReadyScenarioScript, formatScenarioFacetLabel } from "@/lib/scenarios/text";
import type { PromptListItem } from "@/lib/types";

type QuickFacetOption = {
  value: string;
  label: string;
};

export type HomeWorkbenchState = {
  query: string;
  setQuery: (value: string) => void;
  selectedTechnique: PromptListItem["technique"] | "all";
  setSelectedTechnique: (value: PromptListItem["technique"] | "all") => void;
  selectedFacet: string | null;
  toggleFacet: (facetValue: string) => void;
  resetFilters: () => void;
  selectedSlug: string | null;
  selectScenarioSlug: (slug: string) => void;
  taskInput: string;
  setTaskInput: (value: string) => void;
  outputDepth: ScenarioResultDepth;
  setOutputDepth: (value: ScenarioResultDepth) => void;
  explorer: ScenarioExplorerSnapshot;
  selectedPrompt: PromptListItem | null;
  techniqueOptions: PromptListItem["technique"][];
  quickFacetOptions: QuickFacetOption[];
  liveResult: string;
  readyScript: string;
  openScenarioHref: string;
  commitRunInput: () => void;
};

export function useHomeWorkbenchState({
  prompts,
  quickUseCases,
  heroPromptBody,
  language,
}: {
  prompts: PromptListItem[];
  quickUseCases: string[];
  heroPromptBody: string | null;
  language: Language;
}): HomeWorkbenchState {
  const [query, setQuery] = useState("");
  const [selectedTechnique, setSelectedTechnique] = useState<PromptListItem["technique"] | "all">("all");
  const [selectedFacet, setSelectedFacet] = useState<string | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(prompts[0]?.slug ?? null);
  const [taskInput, setTaskInput] = useState("");
  const [committedTaskInput, setCommittedTaskInput] = useState("");
  const [outputDepth, setOutputDepth] = useState<ScenarioResultDepth>("detailed");
  const [variationSeed, setVariationSeed] = useState(0);

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
        .filter((option): option is QuickFacetOption => Boolean(option.value)),
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
      taskInput: committedTaskInput,
      outputDepth,
      variationSeed,
    });
  }, [committedTaskInput, explorer.selectedScenario, language, outputDepth, variationSeed]);

  const openScenarioHref = selectedPrompt ? `/prompt/${encodeURIComponent(selectedPrompt.slug)}` : "/catalog";

  return {
    query,
    setQuery,
    selectedTechnique,
    setSelectedTechnique,
    selectedFacet,
    toggleFacet: (facetValue: string) => {
      setSelectedFacet((current) => (current === facetValue ? null : facetValue));
    },
    resetFilters: () => {
      setQuery("");
      setSelectedTechnique("all");
      setSelectedFacet(null);
    },
    selectedSlug,
    selectScenarioSlug: (slug: string) => setSelectedSlug(slug),
    taskInput,
    setTaskInput,
    outputDepth,
    setOutputDepth,
    explorer,
    selectedPrompt,
    techniqueOptions,
    quickFacetOptions,
    liveResult,
    readyScript,
    openScenarioHref,
    commitRunInput: () => {
      setCommittedTaskInput(taskInput);
      setVariationSeed((current) => current + 1);
    },
  };
}
