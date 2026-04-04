import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
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

      <section className="pv-hero px-6 py-8 sm:px-8 sm:py-12">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.08fr)_minmax(280px,360px)] lg:items-center xl:gap-12">
          <div className="pv-hero-copy space-y-7">
            <div className="max-w-[40rem] space-y-4">
              <p className="pv-kicker">
                <T k="home.kicker" />
              </p>
              <h1 className="pv-display max-w-[15ch] text-zinc-950">
                <T k="home.title" />
              </h1>
              <p className="pv-lead max-w-[35rem]">
                <T k="home.subtitle" />
              </p>
            </div>

            <HomeHeroActions initialAuthenticated={Boolean(accessToken)} />
          </div>

          <HeroPreview prompt={heroPrompt} language={language} promptBody={heroPromptBody} />
        </div>
      </section>

      <ShelfSection
        title={promptsTitle}
        href="/catalog"
        hrefLabel={getTranslation(language, "home.seeAll")}
        prompts={featuredPrompts}
        idPrefix="home-featured"
      />

      {popularLessons.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker pv-home-section-kicker">
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

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {popularLessons.map((lesson) => (
              <Link
                key={`home-lesson-${lesson.id}`}
                href={`/learn/${encodeURIComponent(lesson.slug)}`}
                className="pv-card block p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{lesson.title}</p>
                    <p className="mt-2 text-sm text-zinc-600">
                      {lesson.completion_count} <T k="learn.completions" />
                    </p>
                  </div>
                  <span className="pv-chip-brand">
                    <T k={lesson.locked ? "learn.locked" : "learn.open"} />
                  </span>
                </div>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
                  <T k="learn.openLesson" />
                  <span aria-hidden="true">↗</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
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
    <div className="pv-hero-visual">
      <div className="pv-hero-preview-shell">
        <p className="pv-hero-preview-label">{getTranslation(language, "home.previewLabel")}</p>

        <div className="pv-hero-preview-card">
          <span className="pv-chip-brand w-fit">{techniqueLabel}</span>
          <div className="space-y-3">
            <h2 className="pv-hero-preview-title">{previewTitle}</h2>
            <p className="pv-hero-preview-body line-clamp-4">{previewBody}</p>
          </div>

          <details className="pv-hero-preview-dropdown">
            <summary className="pv-hero-preview-foot pv-hero-preview-foot-toggle">
              <span>{getTranslation(language, "home.previewFooter")}</span>
              <svg
                aria-hidden="true"
                viewBox="0 0 20 20"
                className="pv-hero-preview-chevron h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m5.5 8 4.5 4 4.5-4" />
              </svg>
            </summary>

            <div className="pv-hero-preview-dropdown-body">
              <pre className="pv-hero-preview-prompt">{readyPromptTemplate}</pre>
              {prompt ? (
                <Link
                  href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                  className="pv-inline-link text-sm text-[var(--pv-brand-strong)]"
                >
                  {getTranslation(language, "prompt.openPrompt")}
                </Link>
              ) : null}
            </div>
          </details>
        </div>
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
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="catalog.prompts" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        </div>
        <Link href={href} className="pv-inline-link">
          {hrefLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {prompts.map((prompt) => (
          <PromptCard key={`${idPrefix}-${prompt.id}`} prompt={prompt} />
        ))}
      </div>
    </section>
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
