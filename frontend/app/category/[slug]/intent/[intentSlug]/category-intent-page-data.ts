import { fetchPopularLessons, fetchPrompts } from "@/lib/api";
import type { Language } from "@/lib/i18n";
import { pickRelatedLessonsForPrompts } from "@/lib/linking";
import { listCategoryIntentLandings, type CategoryIntentLanding } from "@/lib/seo-landings";
import type { PopularLessonItem, PromptListItem } from "@/lib/types";

export type CategoryIntentResolution = {
  current: CategoryIntentLanding | null;
  siblings: CategoryIntentLanding[];
};

export type CategoryIntentPageData = {
  current: CategoryIntentLanding;
  siblings: CategoryIntentLanding[];
  prompts: PromptListItem[];
  relatedLessons: PopularLessonItem[];
};

export async function resolveCategoryIntentLanding(
  categorySlug: string,
  intentSlug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<CategoryIntentResolution> {
  const landings = await listCategoryIntentLandings({ accessToken, language, minPromptCount: 2 });
  const current = landings.find((item) => item.category_slug === categorySlug && item.intent_slug === intentSlug) ?? null;
  const siblings = landings.filter((item) => item.category_slug === categorySlug && item.intent_slug !== intentSlug);
  return { current, siblings };
}

export async function loadCategoryIntentPageData({
  current,
  siblings,
  accessToken,
  language,
}: {
  current: CategoryIntentLanding;
  siblings: CategoryIntentLanding[];
  accessToken?: string | null;
  language?: Language | string | null;
}): Promise<CategoryIntentPageData> {
  const [prompts, popularLessons] = await Promise.all([
    fetchPrompts({
      category_id: current.category_id,
      use_case: [current.intent_slug],
      sort: "relevance",
      limit: 24,
      accessToken,
      language,
    }),
    fetchPopularLessons({ limit: 12, accessToken, language }),
  ]);

  return {
    current,
    siblings,
    prompts,
    relatedLessons: pickRelatedLessonsForPrompts(prompts, popularLessons, 4),
  };
}
