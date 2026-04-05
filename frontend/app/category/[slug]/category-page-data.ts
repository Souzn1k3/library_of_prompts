import {
  fetchCategories,
  fetchPopularLessons,
  fetchPromptDiscoveryFilters,
  fetchPrompts,
} from "@/lib/api";
import type { Language } from "@/lib/i18n";
import { pickRelatedLessonsForPrompts } from "@/lib/linking";
import type { Category, PopularLessonItem, PromptListItem } from "@/lib/types";

export type CategoryIntentSummary = {
  slug: string;
  name: string;
  count: number;
};

export type CategoryPageData = {
  category: Category;
  trending: PromptListItem[];
  mostSaved: PromptListItem[];
  newest: PromptListItem[];
  intents: CategoryIntentSummary[];
  relatedLessons: PopularLessonItem[];
};

export async function findCategoryBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<Category | null> {
  const categories = await fetchCategories(accessToken, language);
  return categories.find((item) => item.slug === slug) ?? null;
}

async function loadTopIntentsForCategory(
  categoryId: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<CategoryIntentSummary[]> {
  const [filters, prompts] = await Promise.all([
    fetchPromptDiscoveryFilters(accessToken, language),
    fetchPrompts({
      category_id: categoryId,
      limit: 100,
      sort: "most_used",
      accessToken,
      language,
    }),
  ]);

  const nameBySlug = new Map(filters.use_cases.map((item) => [item.slug, item.name]));
  const counts = new Map<string, number>();
  for (const prompt of prompts) {
    for (const slug of prompt.use_cases ?? []) {
      if (!nameBySlug.has(slug)) {
        continue;
      }
      counts.set(slug, (counts.get(slug) ?? 0) + 1);
    }
  }

  return Array.from(counts.entries())
    .filter(([, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([slug, count]) => ({
      slug,
      name: nameBySlug.get(slug) ?? slug,
      count,
    }));
}

export async function loadCategoryPageData({
  category,
  accessToken,
  language,
}: {
  category: Category;
  accessToken?: string | null;
  language?: Language | string | null;
}): Promise<CategoryPageData> {
  const [trending, mostSaved, newest, popularLessons, intents] = await Promise.all([
    fetchPrompts({
      category_id: category.id,
      sort: "trending",
      limit: 16,
      accessToken,
      language,
    }),
    fetchPrompts({
      category_id: category.id,
      sort: "most_saved",
      limit: 6,
      accessToken,
      language,
    }),
    fetchPrompts({
      category_id: category.id,
      sort: "newest",
      limit: 6,
      accessToken,
      language,
    }),
    fetchPopularLessons({ limit: 12, accessToken, language }),
    loadTopIntentsForCategory(category.id, accessToken, language),
  ]);

  return {
    category,
    trending,
    mostSaved,
    newest,
    intents,
    relatedLessons: pickRelatedLessonsForPrompts(trending, popularLessons, 4),
  };
}
