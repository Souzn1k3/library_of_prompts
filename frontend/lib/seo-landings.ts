import { fetchCategories, fetchPromptDiscoveryFilters, fetchPrompts } from "@/lib/api";
import type { Language } from "@/lib/i18n";

export type CategoryIntentLanding = {
  category_id: string;
  category_slug: string;
  category_name: string;
  intent_slug: string;
  intent_name: string;
  prompt_count: number;
  latest_prompt_at: string | null;
};

export async function listCategoryIntentLandings(params?: {
  accessToken?: string | null;
  language?: Language | string | null;
  minPromptCount?: number;
}): Promise<CategoryIntentLanding[]> {
  const minPromptCount = params?.minPromptCount ?? 2;
  const [categories, filters] = await Promise.all([
    fetchCategories(params?.accessToken, params?.language),
    fetchPromptDiscoveryFilters(params?.accessToken, params?.language),
  ]);
  const intentMap = new Map(filters.use_cases.map((item) => [item.slug, item.name]));
  const groups = await Promise.all(
    categories.map(async (category) => {
      const prompts = await fetchPrompts({
        category_id: category.id,
        sort: "most_used",
        limit: 100,
        accessToken: params?.accessToken,
        language: params?.language,
      });

      if (prompts.length < minPromptCount) {
        return [] as CategoryIntentLanding[];
      }

      const bucket = new Map<string, { count: number; latestPromptAt: string | null }>();
      for (const prompt of prompts) {
        const promptDate = prompt.created_at ?? null;
        for (const slug of prompt.use_cases ?? []) {
          if (!intentMap.has(slug)) continue;
          const current = bucket.get(slug);
          if (!current) {
            bucket.set(slug, { count: 1, latestPromptAt: promptDate });
            continue;
          }
          current.count += 1;
          if (!current.latestPromptAt || (promptDate && promptDate > current.latestPromptAt)) {
            current.latestPromptAt = promptDate;
          }
        }
      }

      return Array.from(bucket.entries())
        .filter(([, value]) => value.count >= minPromptCount)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 4)
        .flatMap(([intentSlug, value]) => {
          const intentName = intentMap.get(intentSlug);
          if (!intentName) {
            return [];
          }
          return [
            {
              category_id: category.id,
              category_slug: category.slug,
              category_name: category.name,
              intent_slug: intentSlug,
              intent_name: intentName,
              prompt_count: value.count,
              latest_prompt_at: value.latestPromptAt,
            },
          ];
        });
    }),
  );

  return groups.flat();
}
