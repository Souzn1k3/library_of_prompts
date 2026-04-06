"use client";

import { useMemo } from "react";

import { RenderEngine } from "./render-engine";
import { useScenarioEngineRuntime } from "./use-scenario-engine-runtime";
import type { ScenarioPersistenceAdapter } from "../core/state-engine";
import type {
  ScenarioActionRegistry,
  ScenarioDefinition,
  ScenarioInputField,
  ScenarioTier,
} from "../types";

type ScenarioAppRuntimeProps = {
  definition: ScenarioDefinition;
  actions: ScenarioActionRegistry;
  tier?: ScenarioTier;
  persistenceAdapter?: ScenarioPersistenceAdapter;
  className?: string;
};

export function ScenarioAppRuntime({
  definition,
  actions,
  tier,
  persistenceAdapter,
  className,
}: ScenarioAppRuntimeProps) {
  const runtime = useScenarioEngineRuntime({
    definition,
    actions,
    tier,
    persistenceAdapter,
  });

  const renderEngine = useMemo(() => new RenderEngine(), []);

  const fieldsById = useMemo(() => {
    const map = new Map<string, ScenarioInputField>();
    for (const field of definition.inputs.fields) {
      map.set(field.id, field);
    }
    return map;
  }, [definition.inputs.fields]);

  return (
    <div className={className ?? "pv-page-sm"} data-scenario-app={definition.id}>
      {!runtime.booted ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <p className="text-sm text-zinc-600">Bootstrapping scenario runtime...</p>
        </section>
      ) : null}

      {runtime.snapshot.errors.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-xl font-semibold text-zinc-950">Runtime diagnostics</h2>
          <div className="mt-3 space-y-1">
            {runtime.snapshot.errors.slice(-5).map((error, index) => (
              <p key={`runtime-error-${index}`} className="text-sm text-rose-700">
                {error}
              </p>
            ))}
          </div>
        </section>
      ) : null}

      <main className="space-y-4">
        {renderEngine.render(definition.layout.panels, {
          engine: runtime.core,
          snapshot: runtime.snapshot,
          fieldsById,
        })}
      </main>
    </div>
  );
}
