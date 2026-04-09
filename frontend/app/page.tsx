import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  fetchDiscoverySections,
  fetchPopularLessons,
  fetchPromptBySlug,
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

  const promptsTitle =
    accessToken && homeRecommendations.items.length > 0
      ? getTranslation(language, "dashboard.recommendedForYou")
      : getTranslation(language, "home.trendingPrompts");
  const heroPrompt = featuredPrompts[0];
  const heroPromptBody = heroPrompt
    ? await fetchPromptBySlug(heroPrompt.slug, accessToken, language)
        .then((detail) => (detail.body_locked ? null : detail.body?.trim() || null))
        .catch(() => null)
    : null;

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
            itemListElement: featuredPrompts.slice(0, 6).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(20rem,0.82fr)] xl:items-stretch">
        <section className="pv-hero px-6 py-7 sm:px-8 sm:py-9">
          <div className="space-y-8">
            <div className="max-w-[44rem] space-y-4">
              <p className="pv-kicker">
                <T k="home.kicker" />
              </p>
              <h1 className="pv-display max-w-[13ch] text-zinc-950">
                <T k="home.title" />
              </h1>
              <p className="pv-lead max-w-[36rem]">
                <T k="home.subtitle" />
              </p>
            </div>

            <HomeHeroActions initialAuthenticated={Boolean(accessToken)} />

            <div className="grid gap-3 md:grid-cols-3">
              <ProductModeCard
                title={getTranslation(language, "nav.catalog")}
                body={promptsTitle}
                href="/catalog"
                hrefLabel={getTranslation(language, "home.seeAll")}
              />
              <ProductModeCard
                title={getTranslation(language, "learn.title")}
                body={getTranslation(language, "learn.catalogPathHint")}
                href="/learn"
                hrefLabel={getTranslation(language, "home.viewAllLessons")}
              />
              <ProductModeCard
                title={getTranslation(language, "nav.missions")}
                body={getTranslation(language, "missions.subtitle")}
                href="/missions"
                hrefLabel={getTranslation(language, "nav.missions")}
              />
            </div>
          </div>
        </section>

        <HeroPreview prompt={heroPrompt} language={language} promptBody={heroPromptBody} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                <T k="catalog.prompts" />
              </p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">{promptsTitle}</h2>
              <p className="text-sm leading-relaxed text-zinc-600">
                <T k="home.subtitle" />
              </p>
            </div>
            <Link href="/catalog" className="pv-inline-link">
              <T k="home.seeAll" />
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className="mt-6 grid gap-3">
            {featuredPrompts.slice(0, 4).map((prompt) => (
              <PromptWorkbenchRow key={`home-featured-${prompt.id}`} prompt={prompt} language={language} />
            ))}
          </div>
        </section>

        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">
                <T k="learn.title" />
              </p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">
                <T k="home.popularLessons" />
              </h2>
              <p className="text-sm leading-relaxed text-zinc-600">
                <T k="learn.releaseSubtitle" />
              </p>
            </div>
            <Link href="/learn" className="pv-inline-link">
              <T k="home.viewAllLessons" />
              <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <div className="mt-6 grid gap-3">
            {popularLessons.slice(0, 4).map((lesson, index) => (
              <Link
                key={`home-lesson-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
                      0{index + 1}
                    </p>
                    <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{lesson.title}</p>
                    <p className="text-sm text-zinc-600">
                      {lesson.completion_count} <T k="learn.completions" />
                    </p>
                  </div>
                  <span className="pv-chip-brand shrink-0">
                    <T k={lesson.locked ? "learn.locked" : "learn.open"} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </section>
    </div>
  );
}

function HeroPreview({
  prompt,
  language,
  promptBody,
}: {
  prompt: PromptListItem | undefined;
  language: Language;
  promptBody: string | null;
}) {
  const techniqueLabel = prompt
    ? getTranslation(language, getTechniqueTranslationKey(prompt.technique))
    : getTranslation(language, "catalog.prompts");
  const previewTitle = prompt?.title ?? getTranslation(language, "home.previewEmptyTitle");
  const previewBody = prompt?.summary ?? getTranslation(language, "home.previewEmptyBody");
  const readyPromptTemplate =
    promptBody && promptBody.length > 0
      ? promptBody
      : getHeroStrongPromptFallback(language, previewTitle, previewBody);

  return (
    <aside className="pv-panel flex h-full flex-col gap-4 px-6 py-6 sm:px-7">
      <div className="space-y-2">
        <p className="pv-kicker">{getTranslation(language, "home.previewLabel")}</p>
        <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-950">{previewTitle}</h2>
        <p className="text-sm leading-relaxed text-zinc-600">{previewBody}</p>
      </div>

      <div className="flex flex-wrap gap-2 text-xs text-zinc-600">
        <span className="pv-chip-brand">{techniqueLabel}</span>
        <span className="pv-chip">{getTranslation(language, "catalog.prompts")}</span>
      </div>

      <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/80 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
          {getTranslation(language, "home.previewFooter")}
        </p>
        <pre className="mt-3 whitespace-pre-wrap text-xs leading-6 text-zinc-700">{readyPromptTemplate}</pre>
      </div>

      {prompt ? (
        <Link
          href={`/prompt/${encodeURIComponent(prompt.slug)}`}
          className="pv-button-primary !w-auto self-start"
        >
          {getTranslation(language, "prompt.openPrompt")}
        </Link>
      ) : null}
    </aside>
  );
}

function ProductModeCard({
  title,
  body,
  href,
  hrefLabel,
}: {
  title: string;
  body: string;
  href: string;
  hrefLabel: string;
}) {
  return (
    <Link href={href} className="pv-card block p-4">
      <p className="text-sm font-semibold tracking-[-0.03em] text-zinc-950">{title}</p>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">{body}</p>
      <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
        {hrefLabel}
        <span aria-hidden="true">↗</span>
      </span>
    </Link>
  );
}

function PromptWorkbenchRow({
  prompt,
  language,
}: {
  prompt: PromptListItem;
  language: Language;
}) {
  const techniqueLabel = getTranslation(language, getTechniqueTranslationKey(prompt.technique));

  return (
    <Link href={`/prompt/${encodeURIComponent(prompt.slug)}`} className="pv-card block p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="pv-chip-brand">{techniqueLabel}</span>
            {prompt.is_paid ? <span className="pv-chip">{getTranslation(language, "plans.title")}</span> : null}
          </div>
          <h3 className="text-lg font-semibold tracking-[-0.04em] text-zinc-950">{prompt.title}</h3>
          <p className="text-sm leading-relaxed text-zinc-600">{prompt.summary}</p>
        </div>
        <span className="hidden text-sm font-semibold text-zinc-400 sm:inline">↗</span>
      </div>
    </Link>
  );
}

function getHeroStrongPromptFallback(language: Language, title: string, summary: string) {
  if (language === "ru") {
    return [
      "Ты Senior React Debugger. Помоги найти и исправить баги быстро и безопасно.",
      "",
      `Контекст: ${title}`,
      `Симптом: ${summary}`,
      "",
      "Сделай:",
      "1) Сначала перечисли 3-5 наиболее вероятных причин.",
      "2) Для каждой причины дай шаги проверки (что открыть, что посмотреть, какие логи снять).",
      "3) Покажи минимальный патч для самой вероятной причины.",
      "4) Укажи риски регрессии и как их проверить.",
      "",
      "Формат ответа:",
      "- Гипотезы",
      "- Диагностика",
      "- Патч",
      "- Проверка",
    ].join("\n");
  }

  return [
    "You are a Senior React Debugger. Find and fix bugs fast without regressions.",
    "",
    `Context: ${title}`,
    `Symptom: ${summary}`,
    "",
    "Do this:",
    "1) List the top 3-5 likely root causes first.",
    "2) For each cause, provide concrete validation steps.",
    "3) Provide the minimal patch for the most likely cause.",
    "4) List regression risks and how to test them.",
    "",
    "Response format:",
    "- Hypotheses",
    "- Diagnosis",
    "- Patch",
    "- Verification",
  ].join("\n");
}
