import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { fetchPopularLessons, fetchPrompts } from "@/lib/api";
import { formatTranslation, getTranslation } from "@/lib/i18n";
import { pickRelatedLessonsForPrompts } from "@/lib/linking";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { listCategoryIntentLandings } from "@/lib/seo-landings";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = { params: Promise<{ slug: string; intentSlug: string }> };

export const revalidate = 300;

async function resolveLanding(
  categorySlug: string,
  intentSlug: string,
  accessToken?: string | null,
  language?: string | null,
) {
  const landings = await listCategoryIntentLandings({ accessToken, language, minPromptCount: 2 });
  const current = landings.find((item) => item.category_slug === categorySlug && item.intent_slug === intentSlug);
  const siblings = landings.filter((item) => item.category_slug === categorySlug && item.intent_slug !== intentSlug);
  return { current, siblings };
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug, intentSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const { current } = await resolveLanding(slug, intentSlug, accessToken, language);
  if (!current) {
    return buildPageMetadata({
      title: getTranslation(language, "categoryIntent.metadataFallbackTitle"),
      description: getTranslation(language, "categoryIntent.metadataFallbackDescription"),
      path: `/category/${slug}/intent/${intentSlug}`,
    });
  }
  return buildPageMetadata({
    title: formatTranslation(language, "categoryIntent.metaTitle", {
      intent: current.intent_name,
      category: current.category_name,
    }),
    description: formatTranslation(language, "categoryIntent.metaDescription", {
      intent: current.intent_name,
      category: current.category_name,
    }),
    path: `/category/${current.category_slug}/intent/${current.intent_slug}`,
  });
}

export default async function CategoryIntentPage(props: Props) {
  const { slug, intentSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const { current, siblings } = await resolveLanding(slug, intentSlug, accessToken, language);
  if (!current) notFound();

  const [prompts, popularLessons] = await Promise.all([
    fetchPrompts({
      category_id: current.category_id,
      use_case: [current.intent_slug],
      sort: "relevance",
      limit: 24,
      accessToken,
      language,
    }),
    fetchPopularLessons({ limit: 12, accessToken, language }),
  ]);

  if (prompts.length < 2) {
    notFound();
  }

  const relatedLessons = pickRelatedLessonsForPrompts(prompts, popularLessons, 4);
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

      <header className="space-y-3">
        <Link
          href={`/category/${encodeURIComponent(current.category_slug)}`}
          className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800"
        >
          ← {formatTranslation(language, "categoryIntent.backToCategory", { category: current.category_name })}
        </Link>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">
          {formatTranslation(language, "categoryIntent.heading", {
            intent: current.intent_name,
            category: current.category_name,
          })}
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-zinc-700">
          {formatTranslation(language, "categoryIntent.intro", {
            intent: current.intent_name,
            category: current.category_name,
          })}
        </p>
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
