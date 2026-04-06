import { describe, expect, test } from "vitest";

import { scenarioPlatformActions } from "@/features/scenario-engine";

describe("scenarioPlatformActions", () => {
  test("computes filtered selection snapshot for scenario lists", async () => {
    const result = await scenarioPlatformActions["scenarios.computeSelection"](
      {
        scenarios: [
          {
            id: "1",
            slug: "api-debug",
            title: "API Debug",
            summary: "Debug workflows",
            technique: "other",
            category: "utility",
            facets: ["Debug"],
            qualityScore: 80,
            saveCount: 5,
            copyCount: 1,
            access: {
              freePreviewEnabled: true,
              freeRunsPerDay: 3,
              fullBlueprintRequiresPro: true,
              proCapabilities: [],
            },
            retention: {
              replayReason: "Repeat",
              nextScenarioSlug: null,
              unfinishedActionHint: "Resume",
            },
          },
          {
            id: "2",
            slug: "growth-plan",
            title: "Growth Plan",
            summary: "Scale campaigns",
            technique: "other",
            category: "growth",
            facets: ["Growth"],
            qualityScore: 95,
            saveCount: 12,
            copyCount: 3,
            access: {
              freePreviewEnabled: true,
              freeRunsPerDay: 3,
              fullBlueprintRequiresPro: true,
              proCapabilities: [],
            },
            retention: {
              replayReason: "Repeat",
              nextScenarioSlug: null,
              unfinishedActionHint: "Resume",
            },
          },
        ],
        query: "growth",
        selected_slug: "growth-plan",
      },
      {} as never,
    );

    const output = result as {
      filtered: Array<{ slug: string }>;
      selected: { slug: string } | null;
    };
    expect(output.filtered.length).toBeGreaterThan(0);
    expect(output.selected?.slug).toBe("growth-plan");
  });

  test("builds live result and splits output lines", async () => {
    const result = await scenarioPlatformActions["scenarios.buildLiveResult"](
      {
        language: "en",
        title: "Scenario X",
        summary: "Summary",
        category: "utility",
        task_input: "Investigate conversion drop",
        output_depth: "concise",
      },
      {} as never,
    );

    expect(typeof result).toBe("string");
    const lines = await scenarioPlatformActions["runtime.splitLines"](
      { value: result },
      {} as never,
    );
    expect(Array.isArray(lines)).toBe(true);
    expect((lines as string[]).length).toBeGreaterThan(0);
  });
});
