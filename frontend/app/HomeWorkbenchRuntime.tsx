"use client";

import { useMemo } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ScenarioAppRuntime, scenarioPlatformActions } from "@/features/scenario-engine";
import { buildHomeWorkbenchScenarioDefinition } from "@/features/scenario-engine/scenarios/home/home-workbench-scenario";
import type { PromptListItem } from "@/lib/types";

type HomeWorkbenchRuntimeProps = {
  prompts: PromptListItem[];
};

export function HomeWorkbenchRuntime({ prompts }: HomeWorkbenchRuntimeProps) {
  const { t, language } = useI18n();

  const definition = useMemo(
    () =>
      buildHomeWorkbenchScenarioDefinition({
        prompts,
        language,
        labels: {
          kicker: t("home.entryKicker"),
          title: t("home.entryTitle"),
          subtitle: t("home.entrySubtitle"),
          queryLabel: t("home.entrySearchLabel"),
          queryPlaceholder: t("home.entrySearchPlaceholder"),
          scenarioSelectLabel: t("home.entryLiveResults", { count: prompts.length }),
          taskLabel: t("home.entryIntentLabel"),
          taskPlaceholder: t("home.entryIntentPlaceholder"),
          runNow: t("home.entryRunNow"),
          outputDetailed: t("home.entryOutputDepthDetailed"),
          outputConcise: t("home.entryOutputDepthConcise"),
          refreshResult: t("home.entryRefreshResult"),
          openScenario: t("home.entryPrimaryAction"),
          boostRuns: t("home.entryBoostAction"),
          availableScenarios: t("home.entryLiveResults", { count: prompts.length }),
          liveResultTitle: t("home.entryLiveStageKicker"),
          liveResultSubtitle: t("home.entryLiveStageSubtitle"),
        },
      }),
    [language, prompts, t],
  );

  return (
    <section id="home-workbench">
      <ScenarioAppRuntime definition={definition} actions={scenarioPlatformActions} />
    </section>
  );
}
