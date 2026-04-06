"use client";

import { useMemo } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ScenarioAppRuntime, scenarioPlatformActions } from "@/features/scenario-engine";
import { buildHomeScenariosShowcaseScenarioDefinition } from "@/features/scenario-engine/scenarios/home/home-scenarios-showcase-scenario";
import type {
  PromptListItem,
  ScenarioChainRead,
  ScenarioNextStepRead,
  ScenarioPackRead,
  ScenarioPricingPlanRead,
  ScenarioReturnTriggerRead,
  ScenarioShowcaseRead,
} from "@/lib/types";

export type HomeScenariosRuntimeProps = {
  prompts: PromptListItem[];
  recommendedPrompts: PromptListItem[];
  retentionPrompts: PromptListItem[];
  packs: ScenarioPackRead[];
  chains: ScenarioChainRead[];
  nextSteps: ScenarioNextStepRead[];
  returnTriggers: ScenarioReturnTriggerRead[];
  showcase: ScenarioShowcaseRead[];
  pricingPlans: ScenarioPricingPlanRead[];
  initialAuthenticated: boolean;
};

export function HomeScenariosRuntime(props: HomeScenariosRuntimeProps) {
  const { t, language } = useI18n();

  const definition = useMemo(
    () =>
      buildHomeScenariosShowcaseScenarioDefinition({
        prompts: props.prompts,
        recommendedPrompts: props.recommendedPrompts,
        retentionPrompts: props.retentionPrompts,
        packs: props.packs,
        chains: props.chains,
        nextSteps: props.nextSteps,
        returnTriggers: props.returnTriggers,
        showcase: props.showcase,
        pricingPlans: props.pricingPlans,
        isAuthenticated: props.initialAuthenticated,
        language,
        labels: {
          kicker: t("home.scenarioTryKicker"),
          title: t("home.scenarioTryTitle"),
          subtitle: t("home.scenarioTrySubtitle"),
          openHub: t("home.scenarioCardOpen"),
          labTitle: t("home.scenarioLabTitle"),
          labPlaceholder: t("home.scenarioLabPlaceholder"),
          runNow: t("home.scenarioCardTry"),
          outputDetailed: t("home.entryOutputDepthDetailed"),
          outputConcise: t("home.entryOutputDepthConcise"),
          openScenario: t("home.scenarioCardOpen"),
          openWorkspace: t(props.initialAuthenticated ? "home.entryNextActionSaveAuth" : "home.entryNextActionSaveGuest"),
          packsTitle: t("home.packKicker"),
          chainsTitle: t("home.scenarioChainTitle"),
          retentionTitle: t("home.retentionTitle"),
          nextStepsTitle: t("home.nextStepTitle"),
          returnTitle: t("home.returnTitle"),
          showcaseTitle: t("home.showcaseTitle"),
          pricingTitle: t("home.pricingTitle"),
          pricingStudioAction: t("home.pricingStudioAction"),
          pricingMarketplaceAction: t("home.pricingMarketplaceAction"),
          upgradeAction: t("home.retentionUpgrade"),
        },
      }),
    [
      language,
      props.chains,
      props.initialAuthenticated,
      props.nextSteps,
      props.packs,
      props.pricingPlans,
      props.prompts,
      props.recommendedPrompts,
      props.retentionPrompts,
      props.returnTriggers,
      props.showcase,
      t,
    ],
  );

  return <ScenarioAppRuntime definition={definition} actions={scenarioPlatformActions} />;
}
