import type { Metadata } from "next";
import Link from "next/link";

import { ContributorBadge } from "@/components/ContributorBadge";
import { CatalogFilters } from "@/components/CatalogFilters";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  ApiRequestError,
  fetchCategories,
  fetchTopContributors,
  fetchDiscoverySections,
  fetchPromptDiscoveryFilters,
  fetchPrompts,
} from "@/lib/api";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import type {
  Category,
  ContributorTopItem,
  DiscoverySections,
  PromptDiscoveryFilters,
  PromptListItem,
} from "@/lib/types";

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
  let topContributors: ContributorTopItem[] = [];
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
          (sort as "relevance" | "trending" | "most_used" | "newest" | "most_saved" | undefined) ||
          "relevance",
        accessToken,
        language,
      }),
      fetchPromptDiscoveryFilters(accessToken, language),
    ]);

    if (!hasCustomFilters) {
      [sections, topContributors] = await Promise.all([
        fetchDiscoverySections({ limit: 6, accessToken, language }).catch(
          () => ({ for_you: [], trending: [], best_for_beginners: [], most_saved: [] }),
        ),
        fetchTopContributors({ limit: 8, accessToken, language }).catch(() => []),
      ]);
    }
  } catch (e) {
    if (e instanceof ApiRequestError) {
      error = e.message;
    } else {
      error = getTranslation(language, "catalog.apiUnreachable");
    }
  }

  return (
    <div className="space-y-10">
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

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="catalog.title" />
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">
          <T k="catalog.subtitle" />
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
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

      {categories.length > 0 ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            <T k="catalog.browseCategoryPages" />
          </h2>
          <div className="flex flex-wrap gap-2">
            {categories.slice(0, 12).map((category) => (
              <Link
                key={`category-link-${category.id}`}
                href={`/category/${encodeURIComponent(category.slug)}`}
                className="rounded-full border border-zinc-300 bg-white px-3 py-1 text-xs font-medium text-zinc-800 transition hover:border-zinc-400"
              >
                {category.name}
              </Link>
            ))}
            <Link
              href="/catalog?sort=trending"
              className="rounded-full border border-zinc-900 bg-zinc-900 px-3 py-1 text-xs font-medium text-white transition hover:bg-zinc-800"
            >
              <T k="catalog.discoveryTrending" />
            </Link>
          </div>
        </section>
      ) : null}

      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          <T k="catalog.prompts" />
        </h2>
        {prompts.length === 0 ? (
          <p className="text-sm text-zinc-500">
            <T k="catalog.noPrompts" />
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {prompts.map((p) => (
              <PromptCard key={p.id} prompt={p} />
            ))}
          </div>
        )}
      </section>

      {!hasCustomFilters ? (
        <div className="space-y-8">
          <DiscoverySection
            title={getTranslation(language, "catalog.discoveryForYou")}
            sectionKey="for_you"
            prompts={sections.for_you ?? []}
          />
          <DiscoverySection
            title={getTranslation(language, "catalog.discoveryTrending")}
            sectionKey="trending"
            prompts={sections.trending}
          />
          <DiscoverySection
            title={getTranslation(language, "catalog.discoveryBestForBeginners")}
            sectionKey="best_for_beginners"
            prompts={sections.best_for_beginners}
          />
          <DiscoverySection
            title={getTranslation(language, "catalog.discoveryMostSaved")}
            sectionKey="most_saved"
            prompts={sections.most_saved}
          />
          <TopCreatorsSection items={topContributors} language={language} />
        </div>
      ) : null}
    </div>
  );
}

function DiscoverySection({
  title,
  sectionKey,
  prompts,
}: {
  title: string;
  sectionKey: string;
  prompts: PromptListItem[];
}) {
  if (!prompts.length) return null;
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {prompts.map((p) => (
          <PromptCard key={`${sectionKey}-${p.id}`} prompt={p} />
        ))}
      </div>
    </section>
  );
}

function TopCreatorsSection({ items, language }: { items: ContributorTopItem[]; language: Language }) {
  if (!items.length) return null;
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
        {getTranslation(language, "catalog.topCreators")}
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <Link
            key={item.user_id}
            href={`/contributors/${encodeURIComponent(item.slug)}`}
            className="rounded-lg border border-zinc-200 bg-white p-4 shadow-card transition hover:border-zinc-300"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold text-zinc-900">{item.display_name}</p>
              <ContributorBadge tier={item.reputation_tier} compact />
            </div>
            <p className="mt-1 text-xs text-zinc-600">@{item.slug}</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
              <span>
                {getTranslation(language, "catalog.scoreLabel")}: {item.reputation_score}
              </span>
              <span>
                {getTranslation(language, "catalog.approvedLabel")}: {item.approved_submissions}
              </span>
              <span>
                {getTranslation(language, "catalog.savesLabel")}: {item.total_saves}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
