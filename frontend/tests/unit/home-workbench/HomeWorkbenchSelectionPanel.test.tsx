import React from "react";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HomeWorkbenchSelectionPanel } from "@/app/home-workbench/HomeWorkbenchSelectionPanel";
import type { ScenarioExplorerSnapshot } from "@/features/scenarios/application/scenarioExplorer";
import type { ScenarioDefinition } from "@/features/scenarios/domain/scenario";

const t = (key: string, params?: Record<string, string | number | null | undefined>) =>
  params?.count !== undefined ? `${key}:${params.count}` : key;

function createScenario(id: string, slug: string, title: string): ScenarioDefinition {
  return {
    id,
    slug,
    title,
    summary: `${title} summary`,
    technique: "other",
    category: "utility",
    facets: ["Debugging"],
    qualityScore: 90,
    saveCount: 5,
    copyCount: 2,
    access: {
      freePreviewEnabled: true,
      freeRunsPerDay: 3,
      fullBlueprintRequiresPro: true,
      proCapabilities: ["Save"],
    },
    retention: {
      replayReason: "repeat",
      nextScenarioSlug: null,
      unfinishedActionHint: "resume",
    },
  };
}

describe("HomeWorkbenchSelectionPanel", () => {
  it("triggers selection and run callbacks from the first-screen controls", () => {
    const first = createScenario("1", "scenario-a", "Scenario A");
    const second = createScenario("2", "scenario-b", "Scenario B");
    const explorer: ScenarioExplorerSnapshot = {
      filteredScenarios: [first, second],
      visibleScenarios: [first, second],
      selectedScenario: first,
      hasActiveFilters: false,
    };

    const onRunNow = vi.fn();
    const onSelectScenario = vi.fn();
    const onQueryChange = vi.fn();

    render(
      <HomeWorkbenchSelectionPanel
        t={t as never}
        query=""
        onQueryChange={onQueryChange}
        onRunNow={onRunNow}
        runPending={false}
        selectedTechnique="all"
        onSelectTechnique={vi.fn()}
        techniqueOptions={["other"]}
        quickFacetOptions={[]}
        selectedFacet={null}
        onToggleFacet={vi.fn()}
        explorer={explorer}
        onResetFilters={vi.fn()}
        onSelectScenario={onSelectScenario}
      />,
    );

    fireEvent.change(screen.getByLabelText("home.entrySearchLabel"), {
      target: { value: "API debug" },
    });
    expect(onQueryChange).toHaveBeenCalledWith("API debug");

    fireEvent.click(screen.getByRole("button", { name: "home.entryRunNow" }));
    expect(onRunNow).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /Scenario B/ }));
    expect(onSelectScenario).toHaveBeenCalledWith("scenario-b");
  });

  it("renders graceful no-results fallback with catalog link", () => {
    const explorer: ScenarioExplorerSnapshot = {
      filteredScenarios: [],
      visibleScenarios: [],
      selectedScenario: null,
      hasActiveFilters: true,
    };

    const onResetFilters = vi.fn();
    render(
      <HomeWorkbenchSelectionPanel
        t={t as never}
        query="none"
        onQueryChange={vi.fn()}
        onRunNow={vi.fn()}
        runPending={false}
        selectedTechnique="all"
        onSelectTechnique={vi.fn()}
        techniqueOptions={["other"]}
        quickFacetOptions={[]}
        selectedFacet={null}
        onToggleFacet={vi.fn()}
        explorer={explorer}
        onResetFilters={onResetFilters}
        onSelectScenario={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "home.entryResetFilters" }));
    expect(onResetFilters).toHaveBeenCalledTimes(1);
    expect(screen.getByText("home.entryNoResultsTitle")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /home.entryNoResultsAction/ })).toHaveAttribute("href", "/catalog");
  });
});
