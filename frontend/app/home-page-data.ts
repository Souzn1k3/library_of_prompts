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

  return {
    featuredPrompts,
    promptsTitle,
    popularLessons,
    heroPrompt,
    heroPromptBody,
  };
}
