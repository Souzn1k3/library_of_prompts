import type { ScenarioDefinition } from "../domain/scenario";

const CATEGORY_HINTS: Record<ScenarioDefinition["category"], string[]> = {
  utility: ["debug", "analysis", "bug", "api", "fix", "qa", "audit", "ops"],
  learning: ["learn", "lesson", "teach", "study", "education", "course", "explain"],
  productivity: ["plan", "roadmap", "workflow", "brief", "email", "summary", "standup"],
  entertainment: ["game", "story", "fun", "challenge", "roleplay"],
  growth: ["launch", "growth", "retention", "conversion", "onboarding", "marketing", "sales"],
};

function normalizeTokens(values: Array<string | null | undefined>): string[] {
  return values
    .flatMap((value) => (value ?? "").toLowerCase().replace(/[_-]+/g, " ").split(/\s+/g))
    .map((item) => item.trim())
    .filter(Boolean);
}

function deriveScenarioCategory(prompt: {
  title: string;
  summary?: string | null;
  use_cases?: string[];
  tags?: string[];
}): ScenarioDefinition["category"] {
  const tokens = normalizeTokens([prompt.title, prompt.summary, ...(prompt.use_cases ?? []), ...(prompt.tags ?? [])]);

  let bestCategory: ScenarioDefinition["category"] = "utility";
  let bestScore = -1;

  for (const [category, hints] of Object.entries(CATEGORY_HINTS) as Array<[
    ScenarioDefinition["category"],
    string[],
  ]>) {
    const score = hints.reduce((acc, hint) => (tokens.some((token) => token.includes(hint)) ? acc + 1 : acc), 0);
    if (score > bestScore) {
      bestCategory = category;
      bestScore = score;
    }
  }

  return bestCategory;
}

function toFacetLabel(value: string): string {
  return value
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

export function mapPromptToScenario(prompt: {
  id: string;
  slug: string;
  title: string;
  summary: string | null;
  technique: ScenarioDefinition["technique"];
  use_cases?: string[];
  tags?: string[];
  quality_score?: number;
  save_count?: number;
  copy_count?: number;
}): ScenarioDefinition {
  const category = deriveScenarioCategory(prompt);
  const facets = [...(prompt.use_cases ?? []), ...(prompt.tags ?? [])]
    .map((value) => value.replace(/[_-]+/g, " ").trim())
    .filter(Boolean)
    .slice(0, 5)
    .map(toFacetLabel);

  return {
    id: prompt.id,
    slug: prompt.slug,
    title: prompt.title,
    summary: prompt.summary?.trim() || "Scenario output preview is available instantly.",
    technique: prompt.technique,
    category,
    facets,
    qualityScore: prompt.quality_score ?? 0,
    saveCount: prompt.save_count ?? 0,
    copyCount: prompt.copy_count ?? 0,
    access: {
      freePreviewEnabled: true,
      freeRunsPerDay: 3,
      fullBlueprintRequiresPro: true,
      proCapabilities: [
        "Full blueprint visibility",
        "Unlimited reruns",
        "Scenario customization",
        "Save and chain scenarios",
      ],
    },
    retention: {
      replayReason: "Repeat to improve output quality with your latest context.",
      nextScenarioSlug: null,
      unfinishedActionHint: "Run once now, then save and chain with next scenario.",
    },
  };
}

export function mapPromptListToScenarios<T extends {
  id: string;
  slug: string;
  title: string;
  summary: string | null;
  technique: ScenarioDefinition["technique"];
  use_cases?: string[];
  tags?: string[];
  quality_score?: number;
  save_count?: number;
  copy_count?: number;
}>(prompts: T[]): ScenarioDefinition[] {
  return prompts.map((prompt) => mapPromptToScenario(prompt));
}
