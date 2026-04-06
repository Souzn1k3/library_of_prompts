"use client";

import { useEffect, useMemo, useState } from "react";

import { ScenarioEngineCore } from "../core/scenario-engine-core";
import type { ScenarioPersistenceAdapter } from "../core/state-engine";
import type {
  ScenarioActionRegistry,
  ScenarioDefinition,
  ScenarioRuntimeSnapshot,
  ScenarioTier,
} from "../types";

type UseScenarioEngineRuntimeOptions = {
  definition: ScenarioDefinition;
  actions: ScenarioActionRegistry;
  tier?: ScenarioTier;
  persistenceAdapter?: ScenarioPersistenceAdapter;
};

export function useScenarioEngineRuntime({
  definition,
  actions,
  tier,
  persistenceAdapter,
}: UseScenarioEngineRuntimeOptions) {
  const core = useMemo(
    () =>
      new ScenarioEngineCore({
        definition,
        actions,
        tier,
        persistenceAdapter,
      }),
    [actions, definition, persistenceAdapter, tier],
  );

  const [snapshot, setSnapshot] = useState<ScenarioRuntimeSnapshot>(() => core.getSnapshot());
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    setSnapshot(core.getSnapshot());
    const unsubscribe = core.subscribe(() => {
      setSnapshot(core.getSnapshot());
    });

    void core.boot().finally(() => {
      setBooted(true);
    });

    return () => {
      unsubscribe();
    };
  }, [core]);

  return {
    core,
    snapshot,
    booted,
    triggerInteraction: (interactionId: string, payload?: Record<string, unknown>) =>
      core.triggerInteraction(interactionId, payload),
    dispatch: (eventName: string, payload?: Record<string, unknown>) => core.dispatch(eventName, payload ?? {}),
    undo: () => core.undo(),
    redo: () => core.redo(),
    replay: () => core.replayEvents(),
    resume: () => core.resume(),
    persistNow: () => core.persistNow(),
  };
}
