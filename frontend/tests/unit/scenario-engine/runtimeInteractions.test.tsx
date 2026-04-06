import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScenarioAppRuntime, type ScenarioDefinition } from "@/features/scenario-engine";

const INTERACTION_RUNTIME_DEFINITION: ScenarioDefinition = {
  id: "runtime-interactions-test",
  type: "tool",
  version: 1,
  title: "Runtime Interactions",
  description: "Validate click/keyboard/drag interaction flow",
  layout: {
    panels: [
      {
        id: "runtime-interactions-panel",
        kind: "section",
        renderer: "dom",
        title: "Interaction Surface",
        children: [
          {
            id: "surface-node",
            kind: "text",
            renderer: "dom",
            interactionSource: "surface-zone",
            keyboardFocusable: true,
            draggable: true,
            text: "surface",
          },
          {
            id: "state-clicked",
            kind: "text",
            renderer: "dom",
            text: "clicked={{state.ui.clicked}}",
          },
          {
            id: "state-key",
            kind: "text",
            renderer: "dom",
            text: "key={{state.ui.last_key}}",
          },
          {
            id: "state-drag",
            kind: "text",
            renderer: "dom",
            text: "drag={{state.ui.last_drag}}",
          },
        ],
      },
    ],
  },
  inputs: {
    fields: [],
    interactions: [
      {
        id: "surface-click",
        type: "click",
        source: "surface-zone",
        emits: "surface/click",
      },
      {
        id: "surface-keyboard",
        type: "keyboard",
        source: "surface-zone",
        emits: "surface/keyboard",
        payload: {
          key: { from: "interaction.key" },
        },
      },
      {
        id: "surface-drag",
        type: "drag",
        source: "surface-zone",
        emits: "surface/drag",
        payload: {
          phase: { from: "interaction.phase" },
        },
      },
    ],
  },
  logic: {
    entryEvents: ["app/init"],
    steps: [
      {
        id: "runtime-init",
        on: "app/init",
        actions: [],
      },
      {
        id: "surface-clicked",
        on: "surface/click",
        actions: [{ kind: "set", target: "ui.clicked", value: true }],
      },
      {
        id: "surface-key",
        on: "surface/keyboard",
        actions: [{ kind: "set", target: "ui.last_key", value: { from: "event.payload.key", fallback: "" } }],
      },
      {
        id: "surface-drag",
        on: "surface/drag",
        actions: [{ kind: "set", target: "ui.last_drag", value: { from: "event.payload.phase", fallback: "" } }],
      },
    ],
  },
  output: {
    renderer: "dom",
    liveUpdates: true,
  },
  state: {
    variables: [
      { scope: "ui", key: "clicked", initial: false },
      { scope: "ui", key: "last_key", initial: "-" },
      { scope: "ui", key: "last_drag", initial: "-" },
    ],
    persistence: {
      key: "runtime-interactions-test",
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

describe("Scenario runtime interactions", () => {
  it("routes click, keyboard, and drag events through DSL interactions", async () => {
    render(<ScenarioAppRuntime definition={INTERACTION_RUNTIME_DEFINITION} actions={{}} />);

    const surface = await screen.findByText("surface");
    expect(surface).toHaveAttribute("tabindex", "0");
    expect(surface).toHaveAttribute("draggable", "true");

    fireEvent.click(surface);
    expect(await screen.findByText("clicked=true")).toBeInTheDocument();

    fireEvent.keyDown(surface, { key: "K", code: "KeyK" });
    expect(await screen.findByText("key=K")).toBeInTheDocument();

    fireEvent.dragStart(surface, { clientX: 5, clientY: 8 });
    fireEvent.drop(surface, { clientX: 10, clientY: 12 });
    expect(await screen.findByText("drag=drop")).toBeInTheDocument();
  });
});
