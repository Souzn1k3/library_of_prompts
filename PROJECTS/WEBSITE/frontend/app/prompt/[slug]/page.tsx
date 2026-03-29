import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { PromptViewTracker } from "@/components/analytics/PromptViewTracker";
import { TrackedUpgradeButton } from "@/components/analytics/TrackedUpgradeButton";
import { CopyPromptButton } from "@/components/CopyPromptButton";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { SavePromptButton } from "@/components/SavePromptButton";
import { JsonLd } from "@/components/seo/JsonLd";
import { LmnAmount } from "@/components/ui/LmnAmount";
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
    const relatedLessons = pickRelatedLessonsForPrompts([prompt], popularLessons, 2);
    const primaryLesson = relatedLessons[0] ?? null;
    const interactionMetadata = {
      prompt_slug: prompt.slug,
      category_slug: category?.slug ?? null,
      contributor_slug: prompt.contributor_slug ?? null,
    };

    return (
      <article className="pv-page-sm">
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
          }}
        />

        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "nav.catalog"), href: "/catalog" },
            ...(category
              ? [
                  {
                    label: category.name,
                    href: `/category/${encodeURIComponent(category.slug)}`,
                  },
                ]
              : []),
            { label: prompt.title },
          ]}
          eyebrow={getTranslation(language, "prompt.sectionTitle")}
          title={prompt.title}
          description={prompt.summary ?? undefined}
        >
          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
            <span className="font-medium text-zinc-700">
              {getTranslation(language, getTechniqueTranslationKey(prompt.technique))}
            </span>
            {prompt.difficulty ? (
              <span>
                · {getTranslation(language, getDifficultyTranslationKey(prompt.difficulty))}
              </span>
            ) : null}
            {prompt.output_type ? (
              <span>
                · {getTranslation(language, getOutputTypeTranslationKey(prompt.output_type))}
              </span>
            ) : null}
            {category ? <span>· {category.name}</span> : null}
          </div>

          {prompt.body_locked ? (
            <div className="pv-alert pv-alert-warning text-sm">
              <p>{getTranslation(language, "prompt.previewOnlyMessage")}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                <TrackedUpgradeButton
                  href="/pricing?tier=starter"
                  page={`/prompt/${prompt.slug}`}
                  feature="locked_prompt_cta"
                  metadata={{
                    prompt_id: prompt.id,
                    prompt_slug: prompt.slug,
                    target_tier: "starter",
                  }}
                  className="inline-flex pv-button-primary"
                  label={getTranslation(language, "prompt.upgradeToUnlock")}
                />
                {prompt.unlock_offer ? (
                  <Link href="/store" className="pv-button-secondary">
                    {`${getTranslation(language, "prompt.unlockWithLumens")} · ${prompt.unlock_offer.price} ${prompt.unlock_offer.currency}`}
                  </Link>
                ) : null}
              </div>
              {prompt.unlock_offer ? (
                <p className="mt-3 text-xs text-amber-900/80">
                  {prompt.unlock_offer.item_title}
                </p>
              ) : null}
            </div>
          ) : null}
        </PageIntro>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="pv-panel px-6 py-6 sm:px-7">
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-[1.25rem] border border-[var(--pv-border)] bg-white/80 p-5 font-mono text-sm leading-relaxed text-zinc-900">
              {prompt.body}
            </pre>
          </section>

          <aside className="space-y-4">
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">
                {prompt.body_locked
                  ? prompt.unlock_offer
                    ? getTranslation(language, "prompt.unlockWithLumens")
                    : getTranslation(language, "prompt.upgradeToUnlock")
                  : getTranslation(language, "dashboard.tryNow")}
              </p>
              <div className="mt-4 flex flex-col gap-3">
                {!prompt.body_locked ? (
                  <CopyPromptButton promptId={prompt.id} body={prompt.body} metadata={interactionMetadata} />
                ) : null}
                {prompt.body_locked && prompt.unlock_offer ? (
                  <Link href="/store" className="pv-button-primary">
                    <span>{getTranslation(language, "prompt.unlockWithLumens")}</span>
                    <LmnAmount amount={prompt.unlock_offer.price} symbol={prompt.unlock_offer.currency} />
                  </Link>
                ) : null}
                <SavePromptButton promptId={prompt.id} promptSlug={prompt.slug} metadata={interactionMetadata} />
              </div>

              {primaryLesson ? (
                <div className="mt-5 border-t border-[var(--pv-border)] pt-4">
                  <p className="text-sm font-medium text-zinc-950">{primaryLesson.title}</p>
                  <Link
                    href={`/learn/${encodeURIComponent(primaryLesson.slug)}`}
                    className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
                  >
                    {getTranslation(language, "prompt.learnHowItWorks")}
                    <span aria-hidden="true">↗</span>
                  </Link>
                </div>
              ) : null}
            </section>
          </aside>
        </div>

        {related.length > 0 ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <p className="pv-kicker">{getTranslation(language, "prompt.relatedPrompts")}</p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  {getTranslation(language, "prompt.relatedPrompts")}
                </h2>
              </div>
            </div>
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {related.map((item) => (
                <PromptCard key={item.id} prompt={item} />
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
      <div className="pv-alert pv-alert-warning text-sm">
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
