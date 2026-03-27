import type { Metadata } from "next";
import Link from "next/link";

import { T } from "@/components/i18n/T";
import { JsonLd } from "@/components/seo/JsonLd";
import { ApiRequestError, fetchLessons, fetchPopularLessons } from "@/lib/api";
import { getTierTranslationKey, getTranslation } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return buildPageMetadata({
    title: getTranslation(language, "meta.learnTitle"),
    description: getTranslation(language, "meta.learnDescription"),
    path: "/learn",
  });
}

export const revalidate = 120;

export default async function LearnIndexPage() {
  const language = await getServerLanguage();
  let lessons: Awaited<ReturnType<typeof fetchLessons>> = [];
  let popular: Awaited<ReturnType<typeof fetchPopularLessons>> = [];
  let error: string | null = null;
  const accessToken = await getServerAccessToken();
  try {
    [lessons, popular] = await Promise.all([
      fetchLessons(accessToken, language),
      fetchPopularLessons({ limit: 8, accessToken, language }),
    ]);
  } catch (e) {
    error = e instanceof ApiRequestError ? e.message : getTranslation(language, "learn.loadFailed");
  }

  return (
    <div className="space-y-8">
      <JsonLd
        id="ld-learn-index"
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: getTranslation(language, "meta.learnTitle"),
          url: absoluteUrl("/learn"),
          description: getTranslation(language, "meta.learnDescription"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: lessons.slice(0, 20).map((lesson, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: lesson.title,
              url: absoluteUrl(`/learn/${lesson.slug}`),
            })),
          },
        }}
      />

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="learn.title" />
        </h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          <T k="learn.subtitle" />
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {lessons.length === 0 && !error ? (
        <p className="text-sm text-zinc-500">
          <T k="learn.noLessons" />
        </p>
      ) : (
        <>
          <ul className="space-y-3">
            {lessons.map((l) => (
              <li key={l.id}>
                <Link
                  href={`/learn/${encodeURIComponent(l.slug)}`}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm shadow-card transition hover:border-zinc-300"
                >
                  <span className="font-medium text-zinc-900">{l.title}</span>
                  <span className="text-xs text-zinc-500">
                    {l.locked ? <T k="learn.locked" /> : <T k="learn.open" />} ·{" "}
                    {getTranslation(language, getTierTranslationKey(l.min_tier))}
                  </span>
                </Link>
              </li>
            ))}
          </ul>

          {popular.length > 0 ? (
            <section className="space-y-3">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
                <T k="learn.popularLessons" />
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {popular.slice(0, 6).map((lesson) => (
                  <Link
                    key={`popular-${lesson.id}`}
                    href={`/learn/${encodeURIComponent(lesson.slug)}`}
                    className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm transition hover:border-zinc-300"
                  >
                    <p className="font-medium text-zinc-900">{lesson.title}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {lesson.completion_count} <T k="learn.completions" /> ·{" "}
                      {lesson.locked ? <T k="learn.locked" /> : <T k="learn.open" />}
                    </p>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
