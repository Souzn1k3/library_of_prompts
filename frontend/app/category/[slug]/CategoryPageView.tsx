import Link from "next/link";

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
    <div className="space-y-8">
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

      <header className="space-y-3">
        <Link href="/catalog" className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800">
          ← {getTranslation(language, "category.backToCatalog")}
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
          {category.name} {getTranslation(language, "category.promptsSuffix")}
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-zinc-700">
          {formatTranslation(language, "category.intro", { category: category.name })}
        </p>
      </header>

      {intents.length ? (
        <section className="space-y-3 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h2 className="text-sm font-semibold text-zinc-900">
            {getTranslation(language, "category.popularIntents")}
          </h2>
          <p className="text-xs text-zinc-600">
            {getTranslation(language, "category.popularIntentsBody")}
          </p>
          <div className="flex flex-wrap gap-2">
            {intents.map((intent) => (
              <Link
                key={`${category.slug}-${intent.slug}`}
                href={`/category/${encodeURIComponent(category.slug)}/intent/${encodeURIComponent(intent.slug)}`}
                className="rounded-full border border-zinc-300 bg-white px-3 py-1 text-xs font-medium text-zinc-800 transition hover:border-zinc-400"
              >
                {intent.name} ({intent.count})
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          {formatTranslation(language, "category.trendingIn", { category: category.name })}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {trending.map((prompt) => (
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      </section>

      {mostSaved.length ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {getTranslation(language, "category.mostSaved")}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {mostSaved.map((prompt) => (
              <PromptCard key={`saved-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {newest.length ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {formatTranslation(language, "category.newestIn", { category: category.name })}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {newest.map((prompt) => (
              <PromptCard key={`new-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {relatedLessons.length ? (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {getTranslation(language, "category.relatedLessons")}
          </h2>
          <p className="text-sm text-zinc-600">
            {getTranslation(language, "category.relatedLessonsBody")}
          </p>
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
