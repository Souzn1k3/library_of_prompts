import { describe, expect, test, vi } from "vitest";

import { ScenarioEngineCore, type ScenarioDefinition } from "@/features/scenario-engine";

const TEST_DEFINITION: ScenarioDefinition = {
  id: "test-scenario",
  type: "tool",
  version: 1,
  title: "Test Scenario",
  description: "DSL runtime smoke test",
  layout: {
    panels: [
      {
        id: "hero",
        kind: "hero",
        renderer: "dom",
        title: "Test",
      },
    ],
  },
  inputs: {
    fields: [
      {
        id: "field-one",
        formId: "main",
        label: "Field",
        type: "text",
        bind: "local.forms.main.value",
        interactionId: "field.update",
      },
    ],
    interactions: [
      {
        id: "field.update",
        type: "input",
        source: "field-one",
        emits: "form/update",
        payload: {
          bind: { from: "interaction.bind" },
          value: { from: "interaction.value" },
        },
      },
      {
        id: "form.submit",
        type: "submit",
        source: "main",
        emits: "form/submit",
      },
    ],
  },
  logic: {
    entryEvents: ["app/init"],
    steps: [
      {
        id: "init",
        on: "app/init",
        actions: [{ kind: "set", target: "ui.status", value: "ready" }],
      },
      {
        id: "field-update",
        on: "form/update",
        actions: [{ kind: "set_path", targetFrom: "bind", valueFrom: "value" }],
      },
      {
        id: "submit",
        on: "form/submit",
        actions: [
          {
            kind: "invoke",
            actionId: "test.submit",
            input: {
              value: { from: "state.local.forms.main.value" },
            },
            assign: "ui.result",
          },
        ],
      },
    ],
  },
  output: {
    renderer: "dom",
    liveUpdates: true,
  },
  state: {
    variables: [
      { scope: "ui", key: "status", initial: "idle" },
      { scope: "ui", key: "result", initial: null },
      { scope: "streams", key: "activity", initial: [] },
    ],
    persistence: {
      key: "test-scenario",
      local: false,
      server: false,
    },
    enableUndoRedo: true,
    enableReplay: true,
    resumeEvent: "app/init",
  },
  permissions: {
    defaultTier: "free",
    gates: [],
    usageLimits: [],
  },
  composition: {
    sharedState: [{ from: "local.forms.main.value", to: "global.shared.form_value" }],
  },
  sandbox: {
    allowedActions: ["test.submit"],
    maxActionMs: 1000,
    maxEventsPerMinute: 100,
  },
};

describe("ScenarioEngineCore", () => {
  test("executes DSL interactions, logic steps, and state updates", async () => {
    const submitAction = vi.fn(async (input: Record<string, unknown>) => ({
      ok: true,
      echoed: input.value,
    }));

    const core = new ScenarioEngineCore({
      definition: TEST_DEFINITION,
      actions: {
        "test.submit": submitAction,
      },
    });

    await core.boot();

    expect(core.getSnapshot().ui.status).toBe("ready");

    await core.triggerInteraction("field.update", {
      bind: "local.forms.main.value",
      value: "hello runtime",
    });
    expect(core.getSnapshot().local.forms.main.value).toBe("hello runtime");
    expect(core.getSnapshot().global.shared).toEqual({ form_value: "hello runtime" });

    await core.triggerInteraction("form.submit", { formId: "main" });
    expect(submitAction).toHaveBeenCalledTimes(1);
    expect(core.getSnapshot().ui.result).toEqual({
      ok: true,
      echoed: "hello runtime",
    });
  });

  test("enforces usage limits without scenario-specific code", async () => {
    const submitAction = vi.fn(async () => ({ ok: true }));
    const definition: ScenarioDefinition = {
      ...TEST_DEFINITION,
      permissions: {
        ...TEST_DEFINITION.permissions,
        usageLimits: [
          {
            id: "submit_limit",
            event: "form/submit",
            max: 1,
            window: "session",
          },
        ],
      },
    };

    const core = new ScenarioEngineCore({
      definition,
      actions: {
        "test.submit": submitAction,
      },
    });

    await core.boot();
    await core.triggerInteraction("form.submit", { formId: "main" });
    await core.triggerInteraction("form.submit", { formId: "main" });

    expect(submitAction).toHaveBeenCalledTimes(1);
    expect(core.getSnapshot().errors.some((message) => message.includes("submit_limit"))).toBe(true);
  });

  test("hydrates local persistence during boot, not constructor render", async () => {
    const definition: ScenarioDefinition = {
      ...TEST_DEFINITION,
      state: {
        ...TEST_DEFINITION.state,
        persistence: {
          key: "runtime-hydration-test",
          local: true,
          server: false,
        },
      },
    };
    const storageKey = "scenario-engine:runtime-hydration-test";
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        local: {
          forms: {
            main: {
              value: "persisted value",
            },
          },
        },
      }),
    );

    try {
      const core = new ScenarioEngineCore({
        definition,
        actions: {
          "test.submit": async () => ({ ok: true }),
        },
      });

      expect(core.getSnapshot().local.forms.main.value).toBe("");

      await core.boot();
      expect(core.getSnapshot().local.forms.main.value).toBe("persisted value");
    } finally {
      window.localStorage.removeItem(storageKey);
    }
  });
});
