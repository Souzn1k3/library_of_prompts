import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import type { CategoryPageData } from "./category-page-data";

type CategoryPageViewProps = {
  language: Language;
  data: CategoryPageData;
};

export function CategoryPageView({ language, data }: CategoryPageViewProps) {
  const { category, trending, mostSaved, newest, intents, relatedLessons } = data;
  const canonical = absoluteUrl(`/category/${category.slug}`);

  return (
    <div className="pv-page">
      <JsonLd
        id={`ld-category-${category.slug}`}
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: formatTranslation(language, "category.metaTitle", { category: category.name }),
          url: canonical,
          description: formatTranslation(language, "category.metaDescription", { category: category.name }),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: trending.slice(0, 10).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
              name: prompt.title,
            })),
          },
        }}
      />

      <PageIntro
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: "/" },
          { label: getTranslation(language, "nav.catalog"), href: "/catalog" },
          { label: category.name },
        ]}
        eyebrow={getTranslation(language, "nav.catalog")}
        title={`${category.name} ${getTranslation(language, "category.promptsSuffix")}`}
        description={formatTranslation(language, "category.intro", { category: category.name })}
        actions={(
          <>
            <Link href="/catalog" className="pv-button-secondary">
              {getTranslation(language, "category.backToCatalog")}
            </Link>
            {intents[0] ? (
              <Link
                href={`/category/${encodeURIComponent(category.slug)}/intent/${encodeURIComponent(intents[0].slug)}`}
                className="pv-button-primary"
              >
                {getTranslation(language, "category.popularIntents")}
              </Link>
            ) : null}
          </>
        )}
        aside={(
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{getTranslation(language, "catalog.prompts")}</p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">{trending.length + mostSaved.length + newest.length}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{getTranslation(language, "category.popularIntents")}</p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">{intents.length}</p>
            </div>
          </div>
        )}
      />

      {intents.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-lg font-semibold text-zinc-900">
            {getTranslation(language, "category.popularIntents")}
          </h2>
          <p className="mt-1 text-sm text-zinc-600">
            {getTranslation(language, "category.popularIntentsBody")}
          </p>
          <div className="mt-4 pv-section-toolbar">
            {intents.map((intent) => (
              <Link
                key={`${category.slug}-${intent.slug}`}
                href={`/category/${encodeURIComponent(category.slug)}/intent/${encodeURIComponent(intent.slug)}`}
                className="pv-segment-button"
              >
                {intent.name} ({intent.count})
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <h2 className="text-xl font-semibold text-zinc-950">
          {formatTranslation(language, "category.trendingIn", { category: category.name })}
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {trending.map((prompt) => (
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      </section>

      {mostSaved.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-xl font-semibold text-zinc-950">
            {getTranslation(language, "category.mostSaved")}
          </h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {mostSaved.map((prompt) => (
              <PromptCard key={`saved-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {newest.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-xl font-semibold text-zinc-950">
            {formatTranslation(language, "category.newestIn", { category: category.name })}
          </h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {newest.map((prompt) => (
              <PromptCard key={`new-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {relatedLessons.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-xl font-semibold text-zinc-950">
            {getTranslation(language, "category.relatedLessons")}
          </h2>
          <p className="mt-1 text-sm text-zinc-600">
            {getTranslation(language, "category.relatedLessonsBody")}
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {relatedLessons.map((lesson) => (
              <Link
                key={lesson.id}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card p-4 text-sm"
              >
                <p className="font-medium text-zinc-900">{lesson.title}</p>
                <p className="mt-1 text-xs text-zinc-500">
                  {lesson.completion_count} {getTranslation(language, "learn.completions")} ·{" "}
                  {lesson.locked
                    ? getTranslation(language, "learn.locked")
                    : getTranslation(language, "learn.open")}
                </p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
