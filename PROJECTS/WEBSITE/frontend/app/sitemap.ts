import type { MetadataRoute } from "next";

import { ApiRequestError, fetchCategories, fetchLessons, fetchPrompts } from "@/lib/api";
import { listCategoryIntentLandings } from "@/lib/seo-landings";
import { getSiteUrl } from "@/lib/site";

export const revalidate = 3600;

const PROMPT_PAGE_SIZE = 100;

async function collectPromptEntries() {
  const rows: Array<{ slug: string; created_at: string }> = [];
  let skip = 0;
  let guard = 0;

  while (guard < 200) {
    const chunk = await fetchPrompts({
      skip,
      limit: PROMPT_PAGE_SIZE,
      sort: "newest",
    });
    if (!chunk.length) break;

    for (const prompt of chunk) {
      rows.push({ slug: prompt.slug, created_at: prompt.created_at });
    }

    if (chunk.length < PROMPT_PAGE_SIZE) break;
    skip += PROMPT_PAGE_SIZE;
    guard += 1;
  }

  return rows;
}

function buildStaticPaths(base: string, now: Date): MetadataRoute.Sitemap {
  return [
    { path: "", priority: 1, changeFrequency: "weekly" as const },
    { path: "/catalog", priority: 0.9, changeFrequency: "daily" as const },
    { path: "/learn", priority: 0.85, changeFrequency: "weekly" as const },
    { path: "/missions", priority: 0.8, changeFrequency: "weekly" as const },
    { path: "/store", priority: 0.7, changeFrequency: "weekly" as const },
    { path: "/wallet", priority: 0.7, changeFrequency: "weekly" as const },
    { path: "/pricing", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/submit", priority: 0.6, changeFrequency: "monthly" as const },
    { path: "/login", priority: 0.4, changeFrequency: "yearly" as const },
    { path: "/signup", priority: 0.5, changeFrequency: "yearly" as const },
    { path: "/dashboard", priority: 0.4, changeFrequency: "weekly" as const },
  ].map(({ path, priority, changeFrequency }) => ({
    url: `${base}${path}`,
    lastModified: now,
    changeFrequency,
    priority,
  }));
}

function isBuildTimeApiFailure(error: unknown): boolean {
  if (error instanceof ApiRequestError) {
    return true;
  }

  if (error instanceof Error) {
    return /fetch failed|ECONNREFUSED|network/i.test(error.message);
  }

  return false;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = getSiteUrl();
  const now = new Date();
  const paths = buildStaticPaths(base, now);

  try {
    const [promptEntries, lessons, categories, categoryIntentLandings] = await Promise.all([
      collectPromptEntries(),
      fetchLessons(),
      fetchCategories(),
      listCategoryIntentLandings({ minPromptCount: 2 }),
    ]);

    const promptUrls: MetadataRoute.Sitemap = promptEntries
      .filter((prompt) => Boolean(prompt.slug))
      .map((prompt) => ({
        url: `${base}/prompt/${encodeURIComponent(prompt.slug)}`,
        lastModified: prompt.created_at ? new Date(prompt.created_at) : now,
        changeFrequency: "weekly",
        priority: 0.8,
      }));

    const lessonUrls: MetadataRoute.Sitemap = lessons
      .filter((lesson) => Boolean(lesson.slug))
      .map((lesson) => ({
        url: `${base}/learn/${encodeURIComponent(lesson.slug)}`,
        lastModified: lesson.created_at ? new Date(lesson.created_at) : now,
        changeFrequency: "weekly",
        priority: 0.75,
      }));

    const categoryUrlResults = await Promise.allSettled(
      categories.map(async (category) => {
        const rows = await fetchPrompts({ category_id: category.id, limit: 1, sort: "newest" });
        if (!rows.length) return null;
        return {
          url: `${base}/category/${encodeURIComponent(category.slug)}`,
          lastModified: rows[0].created_at ? new Date(rows[0].created_at) : now,
          changeFrequency: "weekly" as const,
          priority: 0.8,
        };
      }),
    );

    const categoryUrls = categoryUrlResults
      .filter(
        (
          result,
        ): result is PromiseFulfilledResult<{
          url: string;
          lastModified: Date;
          changeFrequency: "weekly";
          priority: number;
        } | null> => result.status === "fulfilled",
      )
      .map((result) => result.value)
      .filter((row): row is NonNullable<typeof row> => row !== null);

    const categoryIntentUrls: MetadataRoute.Sitemap = categoryIntentLandings.map((landing) => ({
      url: `${base}/category/${encodeURIComponent(landing.category_slug)}/intent/${encodeURIComponent(landing.intent_slug)}`,
      lastModified: landing.latest_prompt_at ? new Date(landing.latest_prompt_at) : now,
      changeFrequency: "weekly",
      priority: 0.76,
    }));

    return [...paths, ...promptUrls, ...lessonUrls, ...categoryUrls, ...categoryIntentUrls];
  } catch (error) {
    if (!isBuildTimeApiFailure(error)) {
      throw error;
    }

    console.warn("[sitemap] API unavailable during build, falling back to static sitemap entries.");
    return paths;
  }
}
