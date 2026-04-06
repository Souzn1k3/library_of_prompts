import {
  fetchDiscoverySections,
  fetchPromptBySlug,
  fetchPromptRecommendations,
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
  const [sections, homeRecommendations] = await Promise.all([
    fetchDiscoverySections({ limit: 8, accessToken, language }).catch(() => ({
      for_you: [],
      trending: [],
      best_for_beginners: [],
      most_saved: [],
    })),
    fetchPromptRecommendations({ context: "home", limit: 8, accessToken, language }).catch(() => ({
      context: "home" as const,
      strategy: "cold_start" as const,
      items: [],
    })),
  ]);

  const recommendedPrompts =
    homeRecommendations.items.length > 0
      ? homeRecommendations.items
      : sections.for_you?.length
        ? sections.for_you
        : sections.trending;

  const entryPrompts = dedupePrompts([
    ...recommendedPrompts,
    ...(sections.trending ?? []),
    ...(sections.best_for_beginners ?? []),
    ...(sections.most_saved ?? []),
  ]).slice(0, 24);

  const retentionPrompts = dedupePrompts([
    ...(sections.most_saved ?? []),
    ...(sections.for_you ?? []),
    ...(sections.trending ?? []),
  ]).slice(0, 8);

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
