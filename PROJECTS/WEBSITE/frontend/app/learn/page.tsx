import type { Metadata } from "next";
import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
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
    <div className="pv-page">
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

      <PageIntro
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: "/" },
          { label: getTranslation(language, "nav.learn") },
        ]}
        eyebrow={<T k="learn.title" />}
        title={<T k="learn.title" />}
        description={<T k="learn.subtitle" />}
        hint={<T k="learn.nextPromptsBody" />}
        actions={
          <>
            <Link href="/catalog" className="pv-button-primary">
              <T k="home.explorePrompts" />
            </Link>
            <Link href={accessToken ? "/dashboard" : "/signup"} className="pv-button-secondary">
              <T k={accessToken ? "nav.dashboard" : "nav.signup"} />
            </Link>
            <Link href="/missions" className="pv-inline-link">
              <T k="nav.missions" />
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
        aside={
          <div className="grid gap-3">
            {popular.slice(0, 3).map((lesson, index) => (
              <Link
                key={`hero-popular-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-zinc-950">{lesson.title}</p>
                    <p className="mt-2 text-xs text-zinc-500">
                      {lesson.completion_count} <T k="learn.completions" /> ·{" "}
                      {lesson.locked ? <T k="learn.locked" /> : <T k="learn.open" />}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-[var(--pv-brand)]">0{index + 1}</span>
                </div>
              </Link>
            ))}
          </div>
        }
      />

      {error ? (
        <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {lessons.length === 0 && !error ? (
        <p className="text-sm text-zinc-500">
          <T k="learn.noLessons" />
        </p>
      ) : (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                <T k="learn.title" />
              </p>
              <h2 className="mt-3 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                <T k="learn.title" />
              </h2>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {lessons.map((lesson) => (
              <Link
                key={lesson.id}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold tracking-[-0.04em] text-zinc-950">{lesson.title}</h3>
                    <p className="mt-3 text-sm text-zinc-600">
                      {getTranslation(language, "learn.minimumTier")}:{" "}
                      {getTranslation(language, getTierTranslationKey(lesson.min_tier))}
                    </p>
                  </div>
                  <span className="pv-chip">
                    {lesson.locked ? <T k="learn.locked" /> : <T k="learn.open" />}
                  </span>
                </div>
                <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]">
                  <T k="home.startLearning" />
                  <span aria-hidden="true">↗</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {popular.length > 3 ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                <T k="learn.popularLessons" />
              </p>
              <h2 className="mt-3 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                <T k="learn.popularLessons" />
              </h2>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {popular.slice(3, 7).map((lesson) => (
              <Link
                key={`popular-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block p-4"
              >
                <p className="text-sm font-semibold text-zinc-950">{lesson.title}</p>
                <p className="mt-2 text-xs text-zinc-500">
                  {lesson.completion_count} <T k="learn.completions" /> ·{" "}
                  {lesson.locked ? <T k="learn.locked" /> : <T k="learn.open" />}
                </p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
