import type { ReactNode } from "react";

import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  fetchDiscoverySections,
  fetchPopularLessons,
} from "@/lib/api";
import { DEFAULT_LANGUAGE } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";
import type { PromptListItem } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const language = DEFAULT_LANGUAGE;

  const [sections, popularLessons] = await Promise.all([
    fetchDiscoverySections({ limit: 4, language }).catch(() => ({
      for_you: [],
      trending: [],
      best_for_beginners: [],
      most_saved: [],
    })),
    fetchPopularLessons({ limit: 4, language }).catch(() => []),
  ]);

  const featuredPrompts = sections.for_you?.length ? sections.for_you : sections.trending;
  const topRecommendedPrompts = featuredPrompts.slice(0, 6);

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

      <section className="pv-hero pv-home-hero-compact px-5 py-4 sm:px-7 sm:py-5">
        <div className="pv-hero-copy max-w-[46rem] space-y-3">
          <p className="pv-kicker">
            <T k="home.kicker" />
          </p>
          <h1 className="max-w-[19ch] text-3xl font-[760] leading-[0.96] tracking-[-0.05em] text-zinc-950 sm:text-4xl xl:text-[2.9rem]">
            <T k="home.title" />
          </h1>
          <p className="pv-lead max-w-[40rem] text-sm leading-relaxed">
            <T k="home.subtitle" />
          </p>
          <p className="text-xs text-zinc-500">
            <T k="home.previewFooter" />
          </p>
          <HomeHeroActions initialAuthenticated={false} />
        </div>
      </section>

      <ShelfSection
        title={<T k="home.trendingPrompts" />}
        href="/catalog"
        hrefLabel={<T k="home.seeAll" />}
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

function ShelfSection({
  title,
  href,
  hrefLabel,
  prompts,
  idPrefix,
}: {
  title: ReactNode;
  href: string;
  hrefLabel: ReactNode;
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
