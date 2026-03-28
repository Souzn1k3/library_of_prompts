import type { Metadata } from "next";
import Link from "next/link";

import { CatalogFilters } from "@/components/CatalogFilters";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  ApiRequestError,
  fetchCategories,
  fetchDiscoverySections,
  fetchPromptDiscoveryFilters,
  fetchPrompts,
} from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import type { Category, DiscoverySections, PromptDiscoveryFilters, PromptListItem } from "@/lib/types";

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return buildPageMetadata({
    title: getTranslation(language, "meta.catalogTitle"),
    description: getTranslation(language, "meta.catalogDescription"),
    path: "/catalog",
  });
}

export const revalidate = 60;

function firstParam(v: string | string[] | undefined): string | undefined {
  if (typeof v === "string") return v;
  if (Array.isArray(v) && v.length > 0) return v[0];
  return undefined;
}

function multiParam(v: string | string[] | undefined): string[] | undefined {
  if (typeof v === "string") return v ? [v] : undefined;
  if (Array.isArray(v) && v.length > 0) return v;
  return undefined;
}

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CatalogPage({ searchParams }: PageProps) {
  const sp = (await searchParams) ?? {};
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const q = firstParam(sp.q);
  const category_id = firstParam(sp.category_id);
  const technique = firstParam(sp.technique);
  const difficulty = firstParam(sp.difficulty);
  const output_type = firstParam(sp.output_type);
  const sort = firstParam(sp.sort);
  const use_case = multiParam(sp.use_case);
  const model = multiParam(sp.model);
  const tag = multiParam(sp.tag);
  const hasCustomFilters = Boolean(
    q ||
      category_id ||
      technique ||
      difficulty ||
      output_type ||
      (use_case && use_case.length > 0) ||
      (model && model.length > 0) ||
      (tag && tag.length > 0) ||
      (sort && sort !== "relevance"),
  );

  let categories: Category[] = [];
  let prompts: PromptListItem[] = [];
  let discoveryFilters: PromptDiscoveryFilters = {
    use_cases: [],
    model_compatibility: [],
    tags: [],
    difficulties: [],
    output_types: [],
    sorts: [],
  };
  let sections: DiscoverySections = { for_you: [], trending: [], best_for_beginners: [], most_saved: [] };
  let error: string | null = null;

  try {
    [categories, prompts, discoveryFilters] = await Promise.all([
      fetchCategories(accessToken, language),
      fetchPrompts({
        limit: 24,
        q: q || undefined,
        category_id: category_id || undefined,
        technique: technique || undefined,
        difficulty: (difficulty as "beginner" | "intermediate" | "advanced" | undefined) || undefined,
        output_type: (output_type as "text" | "code" | "structured" | undefined) || undefined,
        use_case: use_case || undefined,
        model: model || undefined,
        tag: tag || undefined,
        sort:
          (sort as "relevance" | "trending" | "most_used" | "newest" | "most_saved" | undefined) || "relevance",
        accessToken,
        language,
      }),
      fetchPromptDiscoveryFilters(accessToken, language),
    ]);

    if (!hasCustomFilters) {
      sections = await fetchDiscoverySections({ limit: 4, accessToken, language }).catch(() => ({
        for_you: [],
        trending: [],
        best_for_beginners: [],
        most_saved: [],
      }));
    }
  } catch (e) {
    if (e instanceof ApiRequestError) {
      error = e.message;
    } else {
      error = getTranslation(language, "catalog.apiUnreachable");
    }
  }

  const secondaryPrompts = sections.for_you?.length ? sections.for_you : sections.trending;

  return (
    <div className="pv-page">
      <JsonLd
        id="ld-catalog"
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: getTranslation(language, "meta.catalogTitle"),
          url: absoluteUrl("/catalog"),
          description: getTranslation(language, "meta.catalogDescription"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: prompts.slice(0, 20).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <section className="pv-panel px-6 py-7 sm:px-8">
        <div className="max-w-4xl space-y-4">
          <p className="pv-kicker">
            <T k="catalog.title" />
          </p>
          <h1 className="pv-title text-zinc-950">
            <T k="catalog.title" />
          </h1>
          <p className="max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
            <T k="catalog.subtitle" />
          </p>
          <div className="flex flex-wrap gap-2">
            {categories.slice(0, 6).map((category) => (
              <Link
                key={`category-link-${category.id}`}
                href={`/category/${encodeURIComponent(category.slug)}`}
                className="pv-chip"
              >
                {category.name}
              </Link>
            ))}
          </div>
          <Link href="/learn" className="pv-inline-link">
            <T k="home.startLearning" />
            <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </section>

      {error ? (
        <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-medium">
            <T k="catalog.unavailable" />
          </p>
          <p className="mt-1 text-amber-800">{error}</p>
        </div>
      ) : null}

      {!error ? (
        <CatalogFilters
          categories={categories}
          discoveryFilters={discoveryFilters}
          initial={{
            q,
            category_id,
            technique,
            difficulty,
            output_type,
            sort: sort || "relevance",
            use_case,
            model,
            tag,
          }}
        />
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <p className="pv-kicker">
              <T k="catalog.prompts" />
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              <T k="catalog.prompts" />
            </h2>
          </div>
        </div>

        {prompts.length === 0 ? (
          <p className="mt-6 text-sm text-zinc-500">
            <T k="catalog.noPrompts" />
          </p>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {prompts.map((prompt) => (
              <PromptCard key={prompt.id} prompt={prompt} />
            ))}
          </div>
        )}
      </section>

      {!hasCustomFilters && secondaryPrompts.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                {sections.for_you?.length
                  ? getTranslation(language, "catalog.discoveryForYou")
                  : getTranslation(language, "catalog.discoveryTrending")}
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {sections.for_you?.length
                  ? getTranslation(language, "catalog.discoveryForYou")
                  : getTranslation(language, "catalog.discoveryTrending")}
              </h2>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {secondaryPrompts.map((prompt) => (
              <PromptCard key={`secondary-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
