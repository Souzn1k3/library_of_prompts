import Link from "next/link";

import { CatalogFilters } from "@/components/CatalogFilters";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import type { CatalogPageData } from "./catalog-page-data";

type CatalogPageViewProps = {
  language: Language;
  data: CatalogPageData;
};

export function CatalogPageView({ language, data }: CatalogPageViewProps) {
  const { query, categories, prompts, discoveryFilters, sections, error } = data;
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

      <PageIntro
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: "/" },
          { label: getTranslation(language, "nav.catalog") },
        ]}
        eyebrow={<T k="catalog.title" />}
        title={<T k="catalog.title" />}
        description={<T k="catalog.subtitle" />}
        hint={<T k="catalog.browseCategoryPages" />}
        aside={
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">
                <T k="catalog.categories" />
              </p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{categories.length}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">
                <T k="catalog.prompts" />
              </p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{prompts.length}</p>
            </div>
          </div>
        }
      >
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
      </PageIntro>

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
            q: query.q,
            category_id: query.category_id,
            technique: query.technique,
            difficulty: query.difficulty,
            output_type: query.output_type,
            sort: query.sort || "relevance",
            use_case: query.use_case,
            model: query.model,
            tag: query.tag,
          }}
        />
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
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

      {!query.hasCustomFilters && secondaryPrompts.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
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
