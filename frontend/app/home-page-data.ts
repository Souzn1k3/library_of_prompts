import {
  fetchDiscoverySections,
  fetchPopularLessons,
  fetchPromptBySlug,
  fetchPromptRecommendations,
} from "@/lib/api";
import { getTranslation, type Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export type HomePageData = {
  featuredPrompts: PromptListItem[];
  promptsTitle: string;
  popularLessons: Awaited<ReturnType<typeof fetchPopularLessons>>;
  heroPrompt: PromptListItem | undefined;
  heroPromptBody: string | null;
  proof: HomeProofMetrics;
};

export type HomeProofMetrics = {
  promptCount: number;
  totalSaves: number;
  totalCopies: number;
  lessonCount: number;
  topQualityScore: number;
  hasQualitySignals: boolean;
};

export async function loadHomePageData({
  accessToken,
  language,
}: {
  accessToken: string | null | undefined;
  language: Language;
}): Promise<HomePageData> {
  const [sections, popularLessons, homeRecommendations] = await Promise.all([
    fetchDiscoverySections({ limit: 4, accessToken, language }).catch(() => ({
      for_you: [],
      trending: [],
      best_for_beginners: [],
      most_saved: [],
    })),
    fetchPopularLessons({ limit: 4, accessToken, language }).catch(() => []),
    fetchPromptRecommendations({ context: "home", limit: 4, accessToken, language }).catch(() => ({
      context: "home" as const,
      strategy: "cold_start" as const,
      items: [],
    })),
  ]);

  const featuredPrompts =
    homeRecommendations.items.length > 0
      ? homeRecommendations.items
      : sections.for_you?.length
        ? sections.for_you
        : sections.trending;

  const promptsTitle =
    accessToken && homeRecommendations.items.length > 0
      ? getTranslation(language, "dashboard.recommendedForYou")
      : getTranslation(language, "home.trendingPrompts");

  const heroPrompt = featuredPrompts[0];
  const heroPromptBody = heroPrompt
    ? await fetchPromptBySlug(heroPrompt.slug, accessToken, language)
      .then((detail) => (detail.body_locked ? null : detail.body?.trim() || null))
      .catch(() => null)
    : null;

  const promptPool = dedupePrompts([
    ...featuredPrompts,
    ...(sections.trending ?? []),
    ...(sections.best_for_beginners ?? []),
    ...(sections.most_saved ?? []),
  ]);
  const proof = buildProofMetrics(promptPool, popularLessons);

  return {
    featuredPrompts,
    promptsTitle,
    popularLessons,
    heroPrompt,
    heroPromptBody,
    proof,
  };
}

function dedupePrompts(prompts: PromptListItem[]) {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}

function buildProofMetrics(
  prompts: PromptListItem[],
  lessons: Awaited<ReturnType<typeof fetchPopularLessons>>,
): HomeProofMetrics {
  let totalSaves = 0;
  let totalCopies = 0;
  let qualitySignals = 0;
  let topQualityScore = 0;

  for (const prompt of prompts) {
    totalSaves += prompt.save_count ?? 0;
    totalCopies += prompt.copy_count ?? 0;
    if (typeof prompt.quality_score === "number" && prompt.quality_score > 0) {
      qualitySignals += 1;
      topQualityScore = Math.max(topQualityScore, prompt.quality_score);
    }
  }

  return {
    promptCount: prompts.length,
    totalSaves,
    totalCopies,
    lessonCount: lessons.length,
    topQualityScore,
    hasQualitySignals: qualitySignals > 0,
  };
}
