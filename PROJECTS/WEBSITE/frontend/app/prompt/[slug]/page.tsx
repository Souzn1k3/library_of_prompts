import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { PromptViewTracker } from "@/components/analytics/PromptViewTracker";
import { TrackedUpgradeButton } from "@/components/analytics/TrackedUpgradeButton";
import { ContributorBadge } from "@/components/ContributorBadge";
import { CopyPromptButton } from "@/components/CopyPromptButton";
import { PromptCard } from "@/components/PromptCard";
import { SavePromptButton } from "@/components/SavePromptButton";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  ApiRequestError,
  fetchCategories,
  fetchPopularLessons,
  fetchPromptBySlug,
  fetchRelatedPromptsBySlug,
} from "@/lib/api";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getTechniqueTranslationKey,
  getTranslation,
} from "@/lib/i18n";
import { pickRelatedLessonsForPrompts } from "@/lib/linking";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";
import { getServerLanguage } from "@/lib/server-i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import type { PromptListItem } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

const getPromptBySlugCached = cache(
  async (slug: string, accessToken: string | null | undefined, language: string) =>
    fetchPromptBySlug(slug, accessToken, language),
);

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();
  try {
    const prompt = await getPromptBySlugCached(slug, accessToken, language);
    return buildPageMetadata({
      title: prompt.title,
      description: prompt.summary ?? `High-quality prompt: ${prompt.title}`,
      path: `/prompt/${prompt.slug}`,
      type: "article",
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "prompt.metadataFallbackTitle"),
      description: getTranslation(language, "meta.catalogDescription"),
      path: `/prompt/${slug}`,
    });
  }
}

export default async function PromptPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const prompt = await getPromptBySlugCached(slug, accessToken, language);
    const [categories, related, popularLessons] = await Promise.all([
      fetchCategories(accessToken, language),
      fetchRelatedPromptsBySlug(slug, { limit: 4, accessToken, language }).catch(() => [] as PromptListItem[]),
      fetchPopularLessons({ limit: 12, accessToken, language }).catch(() => []),
    ]);

    const category = categories.find((item) => item.id === prompt.category_id);
    const relatedLessons = pickRelatedLessonsForPrompts([prompt], popularLessons, 4);
    const interactionMetadata = {
      prompt_slug: prompt.slug,
      category_slug: category?.slug ?? null,
      contributor_slug: prompt.contributor_slug ?? null,
    };

    return (
      <article className="space-y-8">
        <PromptViewTracker
          promptId={prompt.id}
          promptSlug={prompt.slug}
          bodyLocked={Boolean(prompt.body_locked)}
          categorySlug={category?.slug ?? null}
          contributorSlug={prompt.contributor_slug ?? null}
        />

        <JsonLd
          id={`ld-prompt-${prompt.slug}`}
          data={{
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            name: prompt.title,
            url: absoluteUrl(`/prompt/${prompt.slug}`),
            description: prompt.summary ?? prompt.title,
            author: prompt.contributor_slug
              ? {
                  "@type": "Person",
                  name: prompt.contributor_slug,
                  url: absoluteUrl(`/contributors/${prompt.contributor_slug}`),
                }
              : undefined,
          }}
        />

        <div className="space-y-3">
          <Link
            href="/catalog"
            className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800"
          >
            ← {getTranslation(language, "prompt.backToCatalog")}
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
              {prompt.title}
            </h1>
            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700">
              {getTranslation(language, getTechniqueTranslationKey(prompt.technique))}
            </span>
          </div>
          {prompt.summary ? (
            <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">{prompt.summary}</p>
          ) : null}
          {category ? (
            <p className="text-xs text-zinc-500">
              {getTranslation(language, "prompt.categoryLabel")}:{" "}
              <Link
                href={`/category/${encodeURIComponent(category.slug)}`}
                className="font-medium text-zinc-700 underline"
              >
                {category.name}
              </Link>
            </p>
          ) : null}
          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
            {prompt.difficulty ? (
              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-blue-900">
                {getTranslation(language, getDifficultyTranslationKey(prompt.difficulty))}
              </span>
            ) : null}
            {prompt.output_type ? (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-900">
                {getTranslation(language, getOutputTypeTranslationKey(prompt.output_type))}
              </span>
            ) : null}
            <ContributorBadge tier={prompt.contributor_tier} />
            {prompt.contributor_slug ? (
              <Link
                href={`/contributors/${encodeURIComponent(prompt.contributor_slug)}`}
                className="font-medium text-zinc-700 underline"
              >
                @{prompt.contributor_slug}
              </Link>
            ) : null}
            <span>
              {getTranslation(language, "prompt.savedLabel")}: {prompt.save_count ?? 0}
            </span>
            <span>
              {getTranslation(language, "prompt.copiedLabel")}: {prompt.copy_count ?? 0}
            </span>
            {prompt.contributor_reputation_score != null ? (
              <span>
                {getTranslation(language, "prompt.creatorScoreLabel")}: {prompt.contributor_reputation_score}
              </span>
            ) : null}
            {prompt.quality_score != null ? (
              <span>
                {getTranslation(language, "prompt.qualityLabel")}: {prompt.quality_score}
              </span>
            ) : null}
          </div>
        {prompt.body_locked ? (
          <div className="max-w-2xl space-y-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-950">
            <p>{getTranslation(language, "prompt.previewOnlyMessage")}</p>
              <TrackedUpgradeButton
                href="/plans?tier=starter"
                page={`/prompt/${prompt.slug}`}
                feature="locked_prompt_cta"
                metadata={{
                  prompt_id: prompt.id,
                  prompt_slug: prompt.slug,
                  target_tier: "starter",
                }}
                className="inline-flex items-center justify-center rounded-md bg-amber-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-amber-800"
                label={getTranslation(language, "prompt.upgradeToUnlock")}
              />
            </div>
          ) : null}
        </div>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {getTranslation(language, "prompt.sectionTitle")}
          </h2>
          <pre className="mt-3 whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-mono text-sm leading-relaxed text-zinc-900">
            {prompt.body}
          </pre>
        </section>

        <div className="flex flex-wrap items-start gap-3">
          {!prompt.body_locked ? (
            <CopyPromptButton promptId={prompt.id} body={prompt.body} metadata={interactionMetadata} />
          ) : null}
          <SavePromptButton promptId={prompt.id} promptSlug={prompt.slug} metadata={interactionMetadata} />
        </div>

        {related.length > 0 ? (
          <section className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              {getTranslation(language, "prompt.relatedPrompts")}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {related.map((item) => (
                <PromptCard key={item.id} prompt={item} />
              ))}
            </div>
          </section>
        ) : null}

        {relatedLessons.length > 0 ? (
          <section className="space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              {getTranslation(language, "prompt.relatedLessons")}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {relatedLessons.map((lesson) => (
                <Link
                  key={lesson.id}
                  href={`/learn/${encodeURIComponent(lesson.slug)}`}
                  className="rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm shadow-card transition hover:border-zinc-300"
                >
                  <p className="font-medium text-zinc-900">{lesson.title}</p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {lesson.completion_count} {getTranslation(language, "learn.completions")} ·{" "}
                    {lesson.locked
                      ? getTranslation(language, "learn.locked")
                      : getTranslation(language, "learn.open")}
                  </p>
                </Link>
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
        <p className="font-medium">{getTranslation(language, "prompt.loadFailedTitle")}</p>
        <p className="mt-1 text-amber-800">
          {e instanceof ApiRequestError ? e.message : getTranslation(language, "prompt.unexpectedError")}
        </p>
        <Link href="/catalog" className="mt-3 inline-block text-amber-950 underline">
          {getTranslation(language, "prompt.returnToCatalog")}
        </Link>
      </div>
    );
  }
}
