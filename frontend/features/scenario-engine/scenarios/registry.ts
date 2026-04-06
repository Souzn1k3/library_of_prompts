import { composeScenarioDefinitions } from "../core/layout-engine";
import type { ScenarioDefinition } from "../types";
import { growthOpsScenario } from "./analytics/growth-scenario";
import { gtmOpsScenario } from "./analytics/gtm-scenario";
import { revenueOpsScenario } from "./analytics/revenue-scenario";

const SCENARIO_REGISTRY: Record<string, ScenarioDefinition> = {
  [growthOpsScenario.id]: growthOpsScenario,
  [revenueOpsScenario.id]: revenueOpsScenario,
  [gtmOpsScenario.id]: gtmOpsScenario,
};

export function getScenarioDefinition(scenarioId: string): ScenarioDefinition | null {
  return SCENARIO_REGISTRY[scenarioId] ?? null;
}

export function listScenarioDefinitions(): ScenarioDefinition[] {
  return Object.values(SCENARIO_REGISTRY);
}

export function getComposedScenarioDefinition(scenarioId: string): ScenarioDefinition | null {
  const base = getScenarioDefinition(scenarioId);
  if (!base) {
    return null;
  }

  const pipeline = base.composition?.pipeline ?? [];
  const children = pipeline
    .filter((item) => item !== base.id)
    .map((item) => getScenarioDefinition(item))
    .filter((item): item is ScenarioDefinition => Boolean(item));

  if (!children.length) {
    return base;
  }

  return composeScenarioDefinitions(base, children);
}
