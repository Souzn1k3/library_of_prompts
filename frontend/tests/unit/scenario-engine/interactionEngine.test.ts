import { describe, expect, it, vi } from "vitest";

import type { ScenarioDefinition, ScenarioRuntimeSnapshot } from "@/features/scenario-engine";
import { InteractionEngine } from "@/features/scenario-engine/core/interaction-engine";

const BASE_DEFINITION: ScenarioDefinition = {
  id: "interaction-engine-test",
  type: "tool",
  version: 1,
  title: "Interaction Engine Test",
  description: "interaction dispatch by type + source",
  layout: { panels: [] },
  inputs: {
    fields: [],
    interactions: [
      {
        id: "zone-click",
        type: "click",
        source: "zone",
        emits: "zone/click",
      },
      {
        id: "zone-keyboard",
        type: "keyboard",
        source: "zone",
        emits: "zone/keyboard",
        payload: {
          key: { from: "interaction.key" },
        },
      },
      {
        id: "zone-drag",
        type: "drag",
        source: "zone",
        emits: "zone/drag",
        payload: {
          phase: { from: "interaction.phase" },
        },
      },
    ],
  },
  logic: {
    entryEvents: [],
    steps: [],
  },
  output: {
    renderer: "dom",
    liveUpdates: true,
  },
  state: {
    variables: [],
    persistence: {
      key: "interaction-engine-test",
      local: false,
      server: false,
    },
  },
  permissions: {
    defaultTier: "free",
    gates: [],
    usageLimits: [],
  },
  sandbox: {
    allowedActions: [],
  },
};

function createSnapshot(): ScenarioRuntimeSnapshot {
  return {
    global: {},
    local: {},
    session: {},
    ui: {},
    streams: {},
    usage: {},
    errors: [],
    replay: [],
    meta: {
      lastEvent: null,
      eventCount: 0,
      lastUpdatedAt: null,
    },
  };
}

describe("InteractionEngine", () => {
  it("dispatches interactions by type + source and preserves id-based triggers", async () => {
    const dispatch = vi.fn(async () => undefined);
    const engine = new InteractionEngine({
      definition: BASE_DEFINITION,
      dispatch,
      getSnapshot: () => createSnapshot(),
    });

    expect(engine.hasInteraction("keyboard", "zone")).toBe(true);
    expect(engine.hasInteraction("keyboard", "missing-zone")).toBe(false);

    await engine.triggerByTypeAndSource("keyboard", "zone", { key: "Enter" });
    expect(dispatch).toHaveBeenNthCalledWith(1, "zone/keyboard", { key: "Enter" });

    await engine.triggerByTypeAndSource("drag", "zone", { phase: "drop" });
    expect(dispatch).toHaveBeenNthCalledWith(2, "zone/drag", { phase: "drop" });

    await engine.triggerByTypeAndSource("click", "missing-zone");
    expect(dispatch).toHaveBeenCalledTimes(2);

    await engine.trigger("zone-click", { from: "id-trigger" });
    expect(dispatch).toHaveBeenNthCalledWith(3, "zone/click", { from: "id-trigger" });
  });
});
