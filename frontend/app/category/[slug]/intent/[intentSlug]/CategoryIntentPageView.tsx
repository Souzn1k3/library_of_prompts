import Link from "next/link";

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
    <div className="space-y-8">
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

      <header className="space-y-2">
        <Link
          href={`/category/${encodeURIComponent(current.category_slug)}`}
          className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800"
        >
          ← {formatTranslation(language, "categoryIntent.backToCategory", { category: current.category_name })}
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 sm:text-3xl">
          {formatTranslation(language, "categoryIntent.heading", {
            intent: current.intent_name,
            category: current.category_name,
          })}
        </h1>
      </header>

      {siblings.length ? (
        <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h2 className="text-sm font-semibold text-zinc-900">
            {getTranslation(language, "categoryIntent.exploreNearbyIntents")}
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {siblings.slice(0, 6).map((item) => (
              <Link
                key={`${item.category_slug}-${item.intent_slug}`}
                href={`/category/${encodeURIComponent(item.category_slug)}/intent/${encodeURIComponent(item.intent_slug)}`}
                className="rounded-full border border-zinc-300 bg-white px-3 py-1 text-xs font-medium text-zinc-800 transition hover:border-zinc-400"
              >
                {item.intent_name}
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          {getTranslation(language, "categoryIntent.recommendedPrompts")}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {prompts.map((prompt) => (
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      </section>

      {relatedLessons.length ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {getTranslation(language, "categoryIntent.relatedLessons")}
          </h2>
          <p className="text-sm text-zinc-600">{getTranslation(language, "categoryIntent.relatedLessonsBody")}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {relatedLessons.map((lesson) => (
              <Link
                key={lesson.id}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm shadow-card transition hover:border-zinc-300"
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
