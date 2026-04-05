import Link from "next/link";

import { HomeHeroActions } from "@/components/HomeHeroActions";
import { T } from "@/components/i18n/T";
import { getTechniqueTranslationKey, getTranslation, type Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type HomeHeroSectionProps = {
  language: Language;
  initialAuthenticated: boolean;
  heroPrompt: PromptListItem | undefined;
  heroPromptBody: string | null;
};

export function HomeHeroSection({ language, initialAuthenticated, heroPrompt, heroPromptBody }: HomeHeroSectionProps) {
  return (
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

          <HomeHeroActions initialAuthenticated={initialAuthenticated} />
        </div>

        <HeroPreview prompt={heroPrompt} language={language} promptBody={heroPromptBody} />
      </div>
    </section>
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
