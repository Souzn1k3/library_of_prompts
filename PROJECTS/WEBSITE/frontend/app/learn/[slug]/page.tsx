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
      limit: 6,
      accessToken,
      language,
    }).catch(() => []);

    return (
      <article className="space-y-6">
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

        <Link href="/learn" className="text-xs font-medium text-zinc-500 hover:text-zinc-800">
          ← {getTranslation(language, "learn.backToAll")}
        </Link>
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">{lesson.title}</h1>
          <p className="text-xs text-zinc-500">
            {getTranslation(language, "learn.minimumTier")}:{" "}
            {getTranslation(language, getTierTranslationKey(lesson.min_tier))}
            {lesson.body_locked ? ` · ${getTranslation(language, "learn.previewOnly")}` : ""}
          </p>
          {lesson.body_locked ? (
            <Link
              href={`/plans?tier=${encodeURIComponent(lesson.min_tier)}`}
              className="inline-flex items-center justify-center rounded-md bg-amber-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-amber-800"
            >
              <T k="learn.upgradeToUnlock" />
            </Link>
          ) : null}
        </header>
        <pre className="whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed text-zinc-900">
          {lesson.body}
        </pre>
        {!lesson.body_locked ? (
          <section className="rounded-lg border border-zinc-200 bg-white p-4">
            <p className="mb-2 text-sm text-zinc-700">
              <T k="learn.completeStepBody" />
            </p>
            <CompleteLessonButton slug={lesson.slug} />
          </section>
        ) : null}

        {relatedPrompts.length > 0 ? (
          <section className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              <T k="learn.relatedPrompts" />
            </h2>
            <p className="text-sm text-zinc-600">
              <T k="learn.relatedPromptsBody" />
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              {relatedPrompts.map((prompt) => (
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
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {getTranslation(language, "learn.lessonLoadFailed")}
      </div>
    );
  }
}
