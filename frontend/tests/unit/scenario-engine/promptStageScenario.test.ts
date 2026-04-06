import { describe, expect, test } from "vitest";

import { buildPromptStageScenarioDefinition } from "@/features/scenario-engine/scenarios/prompt/prompt-stage-scenario";

describe("buildPromptStageScenarioDefinition", () => {
  test("creates runtime DSL for prompt stage with run/boost interactions", () => {
    const definition = buildPromptStageScenarioDefinition({
      promptSlug: "scenario-stage",
      title: "Scenario Stage",
      summary: "Summary",
      category: "utility",
      bodyLocked: true,
      language: "en",
    });

    expect(definition.id).toBe("prompt-stage:scenario-stage");
    expect(definition.inputs.interactions.some((interaction) => interaction.id === "prompt-stage-run")).toBe(true);
    expect(definition.inputs.interactions.some((interaction) => interaction.id === "prompt-stage-boost")).toBe(true);
    expect(definition.logic.steps.some((step) => step.on === "prompt/run")).toBe(true);
    expect(definition.logic.steps.some((step) => step.on === "prompt/boost")).toBe(true);
    expect(definition.sandbox?.allowedActions.includes("scenarios.trackDemoRun")).toBe(true);
  });

  test("switches lock section content for unlocked prompts", () => {
    const unlocked = buildPromptStageScenarioDefinition({
      promptSlug: "scenario-stage",
      title: "Scenario Stage",
      summary: "Summary",
      category: "utility",
      bodyLocked: false,
      language: "en",
    });

    const lockSection = unlocked.layout.panels.find((panel) => panel.id === "prompt-stage-gate");
    expect(lockSection && "subtitle" in lockSection ? lockSection.subtitle : "").toContain("customize");
  });
});
