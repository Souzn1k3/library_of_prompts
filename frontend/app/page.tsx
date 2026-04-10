import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  fetchDiscoverySections,
  fetchPopularLessons,
  fetchPromptRecommendations,
} from "@/lib/api";
import { getTechniqueTranslationKey, getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";
import type { PromptListItem } from "@/lib/types";

export const revalidate = 180;

export default async function HomePage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const [sections, popularLessons, homeRecommendations] = await Promise.all([
    fetchDiscoverySections({ limit: 4, accessToken, language }).catch(() => ({
      for_you: [],
      trending: [],
      best_for_beginners: [],
      most_saved: [],
    })),
    fetchPopularLessons({ limit: 4, accessToken, language }).catch(() => []),
    fetchPromptRecommendations({ context: "home", limit: 4, accessToken, language }).catch(() => ({
      context: "home" as const,
      strategy: "cold_start" as const,
      items: [],
    })),
  ]);

  const featuredPrompts =
    homeRecommendations.items.length > 0
      ? homeRecommendations.items
      : sections.for_you?.length
        ? sections.for_you
        : sections.trending;
  const topRecommendedPrompts = featuredPrompts.slice(0, 6);

  const promptsTitle =
    accessToken && homeRecommendations.items.length > 0
      ? getTranslation(language, "dashboard.recommendedForYou")
      : getTranslation(language, "home.trendingPrompts");

  return (
    <div className="pv-page">
      <JsonLd
        id="ld-home-growth-surfaces"
        data={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          name: "Prompts Vault",
          url: absoluteUrl("/"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: topRecommendedPrompts.map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <section className="pv-hero pv-home-hero-compact px-5 py-5 sm:px-7 sm:py-6">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)] xl:items-start">
          <div className="pv-hero-copy space-y-4">
            <div className="max-w-[36rem] space-y-2.5">
              <p className="pv-kicker">
                <T k="home.kicker" />
              </p>
              <h1 className="max-w-[16ch] text-4xl font-[760] leading-[0.95] tracking-[-0.05em] text-zinc-950 sm:text-5xl xl:text-[3.25rem]">
                <T k="home.title" />
              </h1>
              <p className="pv-lead max-w-[30rem] text-sm leading-relaxed sm:text-[0.95rem]">
                <T k="home.subtitle" />
              </p>
            </div>

            <HomeHeroActions initialAuthenticated={Boolean(accessToken)} />
          </div>

          <HeroRecommendationsPanel
            title={promptsTitle}
            prompts={topRecommendedPrompts.slice(0, 3)}
            language={language}
          />
        </div>
      </section>

      <ShelfSection
        title={promptsTitle}
        href="/catalog"
        hrefLabel={getTranslation(language, "home.seeAll")}
        prompts={topRecommendedPrompts}
        idPrefix="home-featured"
      />

      {popularLessons.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                <T k="learn.title" />
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                <T k="home.popularLessons" />
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">
                <T k="learn.subtitle" />
              </p>
            </div>
            <Link href="/learn" className="pv-inline-link">
              <T k="home.viewAllLessons" />
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className="mt-6 space-y-3">
            {popularLessons.map((lesson) => (
              <Link
                key={`home-lesson-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block px-5 py-4 sm:px-6"
              >
                <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-center">
                  <div className="min-w-0">
                    <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{lesson.title}</p>
                    <p className="mt-2 text-sm text-zinc-600">
                      {lesson.completion_count} <T k="learn.completions" />
                    </p>
                  </div>
                  <span className="pv-chip-brand w-fit">
                    <T k={lesson.locked ? "learn.locked" : "learn.open"} />
                  </span>

                  <span className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)] md:justify-self-end">
                    <T k="learn.openLesson" />
                    <span aria-hidden="true">↗</span>
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function HeroRecommendationsPanel({
  title,
  prompts,
  language,
}: {
  title: string;
  prompts: PromptListItem[];
  language: Language;
}) {
  return (
    <div className="pv-hero-visual">
      <div className="pv-card p-4 sm:p-5">
        <p className="pv-kicker">
          <T k="home.personalizedKicker" />
        </p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-600">
          <T k="home.personalizedSubtitle" />
        </p>

        <div className="mt-4 space-y-2.5">
          {prompts.length ? (
            prompts.map((prompt, index) => (
              <Link
                key={`hero-reco-${prompt.id}`}
                href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                className="group block rounded-[1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] px-3 py-3 transition hover:border-[var(--pv-border-strong)] hover:bg-white"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="pv-chip-brand text-[11px]">#{index + 1}</span>
                  <span className="pv-chip text-[11px]">
                    {getTranslation(language, getTechniqueTranslationKey(prompt.technique))}
                  </span>
                </div>
                <p className="mt-2 line-clamp-1 text-sm font-semibold tracking-[-0.02em] text-zinc-950 transition group-hover:text-[var(--pv-brand-strong)]">
                  {prompt.title}
                </p>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-zinc-600">
                  {prompt.summary || getTranslation(language, "prompt.noSummary")}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
                  {prompt.recommendation_reason_key ? (
                    <span className="pv-chip">
                      <T k={prompt.recommendation_reason_key} />
                    </span>
                  ) : null}
                  {prompt.quality_score ? (
                    <span className="pv-chip">
                      <T k="prompt.metricQuality" params={{ count: prompt.quality_score }} />
                    </span>
                  ) : null}
                </div>
              </Link>
            ))
          ) : (
            <div className="rounded-[1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] px-3 py-3">
              <p className="text-sm font-semibold text-zinc-950">{getTranslation(language, "home.previewEmptyTitle")}</p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-600">
                {getTranslation(language, "home.previewEmptyBody")}
              </p>
            </div>
          )}
        </div>

        <Link href="/catalog" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
          {getTranslation(language, "home.seeAll")}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}

function ShelfSection({
  title,
  href,
  hrefLabel,
  prompts,
  idPrefix,
}: {
  title: string;
  href: string;
  hrefLabel: string;
  prompts: PromptListItem[];
  idPrefix: string;
}) {
  if (!prompts.length) return null;

  return (
    <section className="pv-panel px-6 py-5 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker">
            <T k="catalog.prompts" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="home.personalizedSubtitle" />
          </p>
        </div>
        <Link href={href} className="pv-inline-link">
          {hrefLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {prompts.map((prompt) => (
          <PromptCard key={`${idPrefix}-${prompt.id}`} prompt={prompt} />
        ))}
      </div>
    </section>
  );
}
