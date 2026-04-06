"use client";

import { ScenarioAppRuntime, scenarioPlatformActions } from "@/features/scenario-engine";
import { mapPromptToScenario } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import type { Language } from "@/lib/i18n";
import type { PromptDetail } from "@/lib/types";

import { buildPromptStageScenarioDefinition } from "@/features/scenario-engine/scenarios/prompt/prompt-stage-scenario";

type PromptScenarioStageRuntimeProps = {
  language: Language;
  prompt: PromptDetail;
};

export function PromptScenarioStageRuntime({ language, prompt }: PromptScenarioStageRuntimeProps) {
  const mapped = mapPromptToScenario(prompt);
  const definition = buildPromptStageScenarioDefinition({
    promptSlug: prompt.slug,
    title: prompt.title,
    summary: prompt.summary ?? mapped.summary,
    category: mapped.category,
    bodyLocked: Boolean(prompt.body_locked),
    language,
  });

  return <ScenarioAppRuntime definition={definition} actions={scenarioPlatformActions} className="pv-page-sm" />;
}
