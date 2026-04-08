import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import type { CategoryIntentPageData } from "./category-intent-page-data";

type CategoryIntentPageViewProps = {
  language: Language;
  data: CategoryIntentPageData;
};

export function CategoryIntentPageView({ language, data }: CategoryIntentPageViewProps) {
  const { current, siblings, prompts, relatedLessons } = data;
  const canonical = absoluteUrl(`/category/${current.category_slug}/intent/${current.intent_slug}`);

  return (
    <div className="pv-page">
      <JsonLd
        id={`ld-category-intent-${current.category_slug}-${current.intent_slug}`}
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: formatTranslation(language, "categoryIntent.metaTitle", {
            intent: current.intent_name,
            category: current.category_name,
          }),
          url: canonical,
          description: formatTranslation(language, "categoryIntent.metaDescription", {
            intent: current.intent_name,
            category: current.category_name,
          }),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: prompts.slice(0, 10).map((prompt, index) => ({
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
          {
            label: current.category_name,
            href: `/category/${encodeURIComponent(current.category_slug)}`,
          },
          { label: current.intent_name },
        ]}
        eyebrow={current.category_name}
        title={formatTranslation(language, "categoryIntent.heading", {
          intent: current.intent_name,
          category: current.category_name,
        })}
        description={formatTranslation(language, "categoryIntent.intro", {
          intent: current.intent_name,
          category: current.category_name,
        })}
        actions={(
          <>
            <Link href={`/category/${encodeURIComponent(current.category_slug)}`} className="pv-button-secondary">
              {formatTranslation(language, "categoryIntent.backToCategory", { category: current.category_name })}
            </Link>
            <Link href="/catalog" className="pv-button-primary">
              {getTranslation(language, "nav.catalog")}
            </Link>
          </>
        )}
        aside={(
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{getTranslation(language, "categoryIntent.recommendedPrompts")}</p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">{prompts.length}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{getTranslation(language, "categoryIntent.exploreNearbyIntents")}</p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">{siblings.length}</p>
            </div>
          </div>
        )}
      />

      {siblings.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-lg font-semibold text-zinc-900">
            {getTranslation(language, "categoryIntent.exploreNearbyIntents")}
          </h2>
          <div className="mt-4 pv-section-toolbar">
            {siblings.slice(0, 6).map((item) => (
              <Link
                key={`${item.category_slug}-${item.intent_slug}`}
                href={`/category/${encodeURIComponent(item.category_slug)}/intent/${encodeURIComponent(item.intent_slug)}`}
                className="pv-segment-button"
              >
                {item.intent_name}
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <h2 className="text-xl font-semibold text-zinc-950">
          {getTranslation(language, "categoryIntent.recommendedPrompts")}
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {prompts.map((prompt) => (
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      </section>

      {relatedLessons.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <h2 className="text-xl font-semibold text-zinc-950">
            {getTranslation(language, "categoryIntent.relatedLessons")}
          </h2>
          <p className="mt-1 text-sm text-zinc-600">{getTranslation(language, "categoryIntent.relatedLessonsBody")}</p>
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
