import type { PromptTechnique } from "@/lib/types";

export type ScenarioCategory =
  | "utility"
  | "learning"
  | "productivity"
  | "entertainment"
  | "growth";

export type ScenarioAccessPolicy = {
  freePreviewEnabled: boolean;
  freeRunsPerDay: number;
  fullBlueprintRequiresPro: boolean;
  proCapabilities: string[];
};

export type ScenarioRetentionPlan = {
  replayReason: string;
  nextScenarioSlug: string | null;
  unfinishedActionHint: string;
};

export type ScenarioDefinition = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  technique: PromptTechnique;
  category: ScenarioCategory;
  facets: string[];
  qualityScore: number;
  saveCount: number;
  copyCount: number;
  access: ScenarioAccessPolicy;
  retention: ScenarioRetentionPlan;
};

export type ScenarioChain = {
  id: string;
  label: string;
  slugs: string[];
};

export type ScenarioResultDepth = "concise" | "detailed";
