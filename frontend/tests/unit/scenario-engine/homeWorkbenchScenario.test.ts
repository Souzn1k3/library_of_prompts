import { describe, expect, test } from "vitest";

import { buildHomeWorkbenchScenarioDefinition } from "@/features/scenario-engine/scenarios/home/home-workbench-scenario";
import type { PromptListItem } from "@/lib/types";

function prompt(input: Partial<PromptListItem> & Pick<PromptListItem, "id" | "slug" | "title">): PromptListItem {
  return {
    id: input.id,
    slug: input.slug,
    title: input.title,
    summary: input.summary ?? "summary",
    status: "published",
    technique: input.technique ?? "other",
    moderation_state: "approved",
    category_id: "cat-1",
    author_id: null,
    created_at: new Date().toISOString(),
    use_cases: input.use_cases ?? [],
    tags: input.tags ?? [],
    quality_score: input.quality_score ?? 80,
    save_count: input.save_count ?? 5,
    copy_count: input.copy_count ?? 2,
  };
}

describe("buildHomeWorkbenchScenarioDefinition", () => {
  test("builds DSL app from prompts with select options and logic events", () => {
    const prompts: PromptListItem[] = [
      prompt({ id: "1", slug: "api-debug", title: "API Debug", use_cases: ["debugging"] }),
      prompt({ id: "2", slug: "growth-plan", title: "Growth Plan", use_cases: ["growth"] }),
    ];

    const definition = buildHomeWorkbenchScenarioDefinition({
      prompts,
      language: "en",
      labels: {
        kicker: "Kicker",
        title: "Workbench",
        subtitle: "Subtitle",
        queryLabel: "Search",
        queryPlaceholder: "Search prompts",
        scenarioSelectLabel: "Scenarios",
        taskLabel: "Task",
        taskPlaceholder: "Describe task",
        runNow: "Run now",
        outputDetailed: "Detailed",
        outputConcise: "Concise",
        refreshResult: "Refresh",
        openScenario: "Open",
        boostRuns: "Boost",
        availableScenarios: "Available scenarios",
        liveResultTitle: "Live output",
        liveResultSubtitle: "Generated result",
      },
    });

    expect(definition.id).toBe("home-workbench-runtime");
    expect(definition.inputs.fields.find((field) => field.id === "home-selected-scenario")?.options?.length).toBe(2);
    expect(definition.logic.steps.some((step) => step.on === "home/run")).toBe(true);
    expect(definition.logic.steps.some((step) => step.on === "home/recompute-selection")).toBe(true);
    expect(definition.permissions.usageLimits.some((limit) => limit.id === "home_run")).toBe(true);
  });
});
