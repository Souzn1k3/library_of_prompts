import { ScenarioRouteRuntime } from "@/components/scenario-engine/ScenarioRouteRuntime";

type ScenarioRuntimePageProps = {
  params: Promise<{ scenarioId: string }>;
};

export default async function ScenarioRuntimePage({ params }: ScenarioRuntimePageProps) {
  const { scenarioId } = await params;
  return <ScenarioRouteRuntime scenarioId={scenarioId} />;
}
