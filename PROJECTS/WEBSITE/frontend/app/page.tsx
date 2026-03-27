import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  fetchDiscoverySections,
  fetchPopularLessons,
  fetchTopContributors,
} from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export const revalidate = 180;

export default async function HomePage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const [sections, topContributors, popularLessons] = await Promise.all([
    fetchDiscoverySections({ limit: 4, accessToken, language }).catch(() => ({
      for_you: [],
      trending: [],
      best_for_beginners: [],
      most_saved: [],
    })),
    fetchTopContributors({ limit: 6, accessToken, language }).catch(() => []),
    fetchPopularLessons({ limit: 6, accessToken, language }).catch(() => []),
  ]);
  const featuredPrompts = sections.for_you?.length ? sections.for_you : sections.trending;

  return (
    <div className="space-y-12">
      <JsonLd
        id="ld-home-growth-surfaces"
        data={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          name: "Prompts Vault",
          url: absoluteUrl("/"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: featuredPrompts.slice(0, 6).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <section className="space-y-6" aria-labelledby="hero-heading">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          <T k="home.kicker" />
        </p>
        <h1
          id="hero-heading"
          className="max-w-2xl text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl"
        >
          <T k="home.title" />
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-zinc-600">
          <T k="home.subtitle" />
        </p>
        <HomeHeroActions />
      </section>

      <section
        className="grid gap-4 sm:grid-cols-3"
        aria-label={getTranslation(language, "home.productHighlightsAria")}
      >
        {[
          {
            id: "structured",
            title: <T k="home.structuredLibraryTitle" />,
            body: <T k="home.structuredLibraryBody" />,
          },
          {
            id: "learn",
            title: <T k="home.builtToLearnTitle" />,
            body: <T k="home.builtToLearnBody" />,
          },
          {
            id: "tool",
            title: <T k="home.seriousToolTitle" />,
            body: <T k="home.seriousToolBody" />,
          },
        ].map((card) => (
          <div
            key={card.id}
            className="rounded-lg border border-zinc-200 bg-zinc-50/60 p-5 shadow-card"
          >
            <h2 className="text-sm font-semibold text-zinc-900">{card.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{card.body}</p>
          </div>
        ))}
      </section>

      {sections.for_you?.length ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="home.smartPicks" />
            </h2>
            <Link href="/catalog" className="text-xs font-medium text-zinc-800 underline">
              <T k="home.seeAll" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {sections.for_you.map((prompt) => (
              <PromptCard key={`home-for-you-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {sections.trending.length ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="home.trendingPrompts" />
            </h2>
            <Link href="/catalog?sort=trending" className="text-xs font-medium text-zinc-800 underline">
              <T k="home.seeAll" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {sections.trending.map((prompt) => (
              <PromptCard key={`home-trending-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {sections.best_for_beginners.length ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="home.bestForBeginners" />
            </h2>
            <Link href="/catalog?difficulty=beginner" className="text-xs font-medium text-zinc-800 underline">
              <T k="home.browseBeginnerPrompts" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {sections.best_for_beginners.map((prompt) => (
              <PromptCard key={`home-beginners-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}

      {topContributors.length ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="home.topContributors" />
            </h2>
            <Link href="/catalog" className="text-xs font-medium text-zinc-800 underline">
              <T k="home.exploreCatalog" />
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {topContributors.map((contributor) => (
              <Link
                key={contributor.user_id}
                href={`/contributors/${encodeURIComponent(contributor.slug)}`}
                className="rounded-lg border border-zinc-200 bg-white p-4 shadow-card transition hover:border-zinc-300"
              >
                <p className="text-sm font-semibold text-zinc-900">{contributor.display_name}</p>
                <p className="mt-1 text-xs text-zinc-500">@{contributor.slug}</p>
                <p className="mt-2 text-xs text-zinc-600">
                  <T k="home.scoreLabel" />: {contributor.reputation_score} · {contributor.approved_submissions}{" "}
                  <T k="home.approvedLabel" /> · {contributor.total_saves} <T k="home.savesLabel" />
                </p>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      {popularLessons.length ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="home.popularLessons" />
            </h2>
            <Link href="/learn" className="text-xs font-medium text-zinc-800 underline">
              <T k="home.viewAllLessons" />
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {popularLessons.map((lesson) => (
              <Link
                key={`home-lesson-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 transition hover:border-zinc-300"
              >
                <p className="text-sm font-semibold text-zinc-900">{lesson.title}</p>
                <p className="mt-1 text-xs text-zinc-500">
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
