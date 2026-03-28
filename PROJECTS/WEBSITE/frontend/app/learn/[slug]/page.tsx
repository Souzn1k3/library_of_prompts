import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { CompleteLessonButton } from "@/components/CompleteLessonButton";
import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { ApiRequestError, fetchLessonBySlug, fetchPrompts } from "@/lib/api";
import { getTierTranslationKey, getTranslation } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";

type Props = { params: Promise<{ slug: string }> };

const getLessonBySlugCached = cache(
  async (slug: string, accessToken: string | null | undefined, language: string) =>
    fetchLessonBySlug(slug, accessToken, language),
);

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();
  try {
    const lesson = await getLessonBySlugCached(slug, accessToken, language);
    return buildPageMetadata({
      title: lesson.title,
      description: `${getTranslation(language, "learn.metadataFallbackTitle")}: ${lesson.title}`,
      path: `/learn/${lesson.slug}`,
      type: "article",
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "learn.metadataFallbackTitle"),
      description: getTranslation(language, "meta.learnDescription"),
      path: `/learn/${slug}`,
    });
  }
}

export default async function LessonPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const lesson = await getLessonBySlugCached(slug, accessToken, language);
    const relatedPrompts = await fetchPrompts({
      q: lesson.title,
      sort: "relevance",
      limit: 4,
      accessToken,
      language,
    }).catch(() => []);

    const primaryPrompt = relatedPrompts[0] ?? null;

    return (
      <article className="pv-page-sm">
        <JsonLd
          id={`ld-lesson-${lesson.slug}`}
          data={{
            "@context": "https://schema.org",
            "@type": "LearningResource",
            name: lesson.title,
            url: absoluteUrl(`/learn/${lesson.slug}`),
            description: `${getTranslation(language, "learn.metadataFallbackTitle")}: ${lesson.title}`,
            educationalLevel: lesson.min_tier,
          }}
        />

        <section className="pv-panel px-6 py-6 sm:px-7">
          <Link href="/learn" className="pv-inline-link">
            <span aria-hidden="true">←</span>
            {getTranslation(language, "learn.backToAll")}
          </Link>

          <div className="mt-5 space-y-4">
            <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span className="font-medium text-zinc-700">
                {getTranslation(language, "learn.minimumTier")}:{" "}
                {getTranslation(language, getTierTranslationKey(lesson.min_tier))}
              </span>
              <span>
                ·{" "}
                {lesson.body_locked
                  ? getTranslation(language, "learn.previewOnly")
                  : getTranslation(language, "learn.open")}
              </span>
            </div>
            <h1 className="pv-title text-zinc-950">{lesson.title}</h1>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="pv-panel px-6 py-6 sm:px-7">
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-[1.25rem] bg-zinc-50 p-5 text-sm leading-relaxed text-zinc-900">
              {lesson.body}
            </pre>
          </section>

          <aside className="space-y-4">
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">
                {lesson.body_locked
                  ? getTranslation(language, "learn.upgradeToUnlock")
                  : getTranslation(language, "learn.completeStepBody")}
              </p>

              {lesson.body_locked ? (
                <Link href={`/pricing?tier=${encodeURIComponent(lesson.min_tier)}`} className="mt-4 inline-flex pv-button-primary">
                  <T k="learn.upgradeToUnlock" />
                </Link>
              ) : (
                <div className="mt-4">
                  <CompleteLessonButton slug={lesson.slug} />
                </div>
              )}

              {primaryPrompt ? (
                <div className="mt-5 border-t border-[var(--pv-border)] pt-4">
                  <p className="text-sm font-medium text-zinc-950">{primaryPrompt.title}</p>
                  <Link
                    href={`/prompt/${encodeURIComponent(primaryPrompt.slug)}`}
                    className="mt-3 inline-flex text-sm font-medium text-[var(--pv-brand)]"
                  >
                    {getTranslation(language, "learn.tryThisPrompt")}
                  </Link>
                </div>
              ) : null}
            </section>
          </aside>
        </div>

        {relatedPrompts.length > 1 ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <p className="pv-kicker">
                  <T k="learn.relatedPrompts" />
                </p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  <T k="learn.relatedPrompts" />
                </h2>
              </div>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {relatedPrompts.slice(1).map((prompt) => (
                <PromptCard key={prompt.id} prompt={prompt} />
              ))}
            </div>
          </section>
        ) : null}
      </article>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    return (
      <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {getTranslation(language, "learn.lessonLoadFailed")}
      </div>
    );
  }
}
