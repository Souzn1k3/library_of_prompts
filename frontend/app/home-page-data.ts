import {
  fetchPromptBySlug,
  fetchScenarioHomeAggregate,
} from "@/lib/api";
import type { Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export type HomePageData = {
  entryPrompts: PromptListItem[];
  recommendedPrompts: PromptListItem[];
  retentionPrompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export async function loadHomePageData({
  accessToken,
  language,
}: {
  accessToken: string | null | undefined;
  language: Language;
}): Promise<HomePageData> {
  const aggregate = await fetchScenarioHomeAggregate({
    accessToken,
    language,
    limit: 8,
  }).catch(() => null);

  const recommendedPrompts = aggregate?.recommended ?? [];
  const entryPrompts = dedupePrompts([
    ...(aggregate?.featured ?? []),
    ...recommendedPrompts,
    ...(aggregate?.retention ?? []),
  ]).slice(0, 24);
  const retentionPrompts = dedupePrompts(aggregate?.retention ?? []).slice(0, 8);

  const heroPrompt = entryPrompts[0];
  const heroPromptBody = heroPrompt
    ? await fetchPromptBySlug(heroPrompt.slug, accessToken, language)
      .then((detail) => (detail.body_locked ? null : detail.body?.trim() || null))
      .catch(() => null)
    : null;

  const quickUseCases = buildQuickUseCases(entryPrompts, 4);

  return {
    entryPrompts,
    recommendedPrompts: recommendedPrompts.slice(0, 6),
    retentionPrompts,
    heroPromptBody,
    quickUseCases,
  };
}

function dedupePrompts(prompts: PromptListItem[]) {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}

function buildQuickUseCases(prompts: PromptListItem[], limit: number): string[] {
  const counts = new Map<string, number>();
  for (const prompt of prompts) {
    for (const candidate of [...(prompt.use_cases ?? []), ...(prompt.tags ?? [])]) {
      const normalized = normalizeQuickUseCase(candidate);
      if (!normalized) {
        continue;
      }
      counts.set(normalized, (counts.get(normalized) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([label]) => label);
}

function normalizeQuickUseCase(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  const normalized = value
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (normalized.length < 3) {
    return null;
  }
  return normalized;
}
