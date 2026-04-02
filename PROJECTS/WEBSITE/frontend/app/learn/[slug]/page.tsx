import type { Metadata } from "next";
import Link from "next/link";
import { cache } from "react";
import { notFound, redirect } from "next/navigation";

import { CompleteLessonButton } from "@/components/CompleteLessonButton";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  ApiRequestError,
  fetchLearningLesson,
  fetchLessonBySlug,
  fetchPrompts,
  locateLearningLessonBySlug,
} from "@/lib/api";
import { getTierTranslationKey, getTranslation } from "@/lib/i18n";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";

type Props = { params: Promise<{ slug: string }> };

const locateCached = cache(
  async (slug: string, accessToken: string | null | undefined, language: string) =>
    locateLearningLessonBySlug(slug, accessToken, language),
);

const getLessonBySlugCached = cache(
  async (slug: string, accessToken: string | null | undefined, language: string) =>
    fetchLessonBySlug(slug, accessToken, language),
);

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();

  try {
    const locate = await locateCached(slug, accessToken, language);
    if (locate) {
      const lesson = await fetchLearningLesson(locate.course_slug, locate.lesson_slug, accessToken, language);
      return buildPageMetadata({
        title: lesson.title,
        description: lesson.summary,
        path: locate.href,
        type: "article",
      });
    }

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

export default async function LegacyLessonCompatibilityPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const locate = await locateCached(slug, accessToken, language);
    if (locate?.href) {
      redirect(locate.href);
    }
  } catch {
    // Keep legacy fallback behavior if new locator is not available.
  }

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
          id={`ld-legacy-lesson-${lesson.slug}`}
          data={{
            "@context": "https://schema.org",
            "@type": "LearningResource",
            name: lesson.title,
            url: absoluteUrl(`/learn/${lesson.slug}`),
            description: `${getTranslation(language, "learn.metadataFallbackTitle")}: ${lesson.title}`,
            educationalLevel: lesson.min_tier,
          }}
        />

        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "nav.learn"), href: "/learn" },
            { label: lesson.title },
          ]}
          eyebrow={getTranslation(language, "learn.title")}
          title={lesson.title}
          description={`${getTranslation(language, "learn.minimumTier")}: ${getTranslation(language, getTierTranslationKey(lesson.min_tier))}`}
          hint={
            lesson.body_locked
              ? getTranslation(language, "learn.previewOnly")
              : getTranslation(language, "learn.open")
          }
        />

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
          <section className="pv-panel px-6 py-6 sm:px-7">
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-[1.25rem] border border-[var(--pv-border)] bg-white/80 p-5 text-sm leading-relaxed text-zinc-900">
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
                    className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
                  >
                    {getTranslation(language, "learn.tryThisPrompt")}
                    <span aria-hidden="true">↗</span>
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
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    return (
      <div className="pv-alert pv-alert-warning text-sm">
        {getTranslation(language, "learn.lessonLoadFailed")}
      </div>
    );
  }
}
