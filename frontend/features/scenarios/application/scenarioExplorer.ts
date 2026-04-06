import type { ScenarioDefinition } from "../domain/scenario";

function normalizeSearchValue(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function scoreScenario(scenario: ScenarioDefinition, normalizedQuery: string): number {
  const title = normalizeSearchValue(scenario.title);
  const summary = normalizeSearchValue(scenario.summary);
  const facets = normalizeSearchValue(scenario.facets.join(" "));
  const category = normalizeSearchValue(scenario.category);

  let score = 0;

  if (title.includes(normalizedQuery)) {
    score += 9;
  }
  if (summary.includes(normalizedQuery)) {
    score += 6;
  }
  if (facets.includes(normalizedQuery)) {
    score += 5;
  }
  if (category.includes(normalizedQuery)) {
    score += 3;
  }

  for (const word of normalizedQuery.split(" ").filter(Boolean)) {
    if (title.includes(word)) {
      score += 2;
    }
    if (summary.includes(word)) {
      score += 1;
    }
  }

  return score;
}

export type ScenarioExplorerState = {
  query: string;
  selectedTechnique: ScenarioDefinition["technique"] | "all";
  selectedFacet: string | null;
  selectedSlug: string | null;
};

export type ScenarioExplorerSnapshot = {
  filteredScenarios: ScenarioDefinition[];
  selectedScenario: ScenarioDefinition | null;
  visibleScenarios: ScenarioDefinition[];
  hasActiveFilters: boolean;
};

const MAX_VISIBLE_SCENARIOS = 6;

export function buildScenarioExplorerSnapshot(
  scenarios: ScenarioDefinition[],
  state: ScenarioExplorerState,
): ScenarioExplorerSnapshot {
  const normalizedQuery = normalizeSearchValue(state.query);
  const normalizedFacet = normalizeSearchValue(state.selectedFacet);

  let filtered = scenarios.filter(
    (scenario) => state.selectedTechnique === "all" || scenario.technique === state.selectedTechnique,
  );

  if (normalizedFacet) {
    filtered = filtered.filter((scenario) =>
      normalizeSearchValue(scenario.facets.join(" ")).includes(normalizedFacet),
    );
  }

  if (normalizedQuery) {
    filtered = filtered
      .map((scenario) => ({
        scenario,
        score: scoreScenario(scenario, normalizedQuery),
      }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map((item) => item.scenario);
  } else {
    filtered = [...filtered].sort((a, b) => {
      const qualityDelta = b.qualityScore - a.qualityScore;
      if (qualityDelta !== 0) {
        return qualityDelta;
      }
      const savesDelta = b.saveCount - a.saveCount;
      if (savesDelta !== 0) {
        return savesDelta;
      }
      return a.title.localeCompare(b.title);
    });
  }

  const selectedScenario =
    (state.selectedSlug
      ? filtered.find((scenario) => scenario.slug === state.selectedSlug) ??
        scenarios.find((scenario) => scenario.slug === state.selectedSlug)
      : null) ??
    filtered[0] ??
    scenarios[0] ??
    null;

  return {
    filteredScenarios: filtered,
    selectedScenario,
    visibleScenarios: filtered.slice(0, MAX_VISIBLE_SCENARIOS),
    hasActiveFilters:
      state.query.trim().length > 0 || state.selectedTechnique !== "all" || Boolean(state.selectedFacet),
  };
}

export function normalizeScenarioFacet(value: string | null | undefined): string | null {
  const normalized = normalizeSearchValue(value);
  if (!normalized || normalized.length < 3) {
    return null;
  }
  return normalized;
}
