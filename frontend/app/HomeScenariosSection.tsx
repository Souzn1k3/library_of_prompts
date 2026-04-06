"use client";

import { HomeScenariosRuntime, type HomeScenariosRuntimeProps } from "./HomeScenariosRuntime";

export type HomeScenariosSectionProps = HomeScenariosRuntimeProps;

export function HomeScenariosSection(props: HomeScenariosSectionProps) {
  return <HomeScenariosRuntime {...props} />;
}
