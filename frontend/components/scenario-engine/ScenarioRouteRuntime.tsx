"use client";

import { useMemo } from "react";

import {
  ScenarioAppRuntime,
  getScenarioDefinition,
  scenarioPlatformActions,
  type ScenarioTier,
} from "@/features/scenario-engine";

type ScenarioRouteRuntimeProps = {
  scenarioId: string;
  tier?: ScenarioTier;
};

export function ScenarioRouteRuntime({ scenarioId, tier }: ScenarioRouteRuntimeProps) {
  const definition = useMemo(() => getScenarioDefinition(scenarioId), [scenarioId]);

  if (!definition) {
    return (
      <div className="pv-page-sm">
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h1 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Scenario not found</h1>
          <p className="mt-2 text-sm text-zinc-600">
            Runtime could not resolve scenario id: {scenarioId}
          </p>
        </section>
      </div>
    );
  }

  return <ScenarioAppRuntime definition={definition} actions={scenarioPlatformActions} tier={tier} />;
}
