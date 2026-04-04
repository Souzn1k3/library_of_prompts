import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { cache } from "react";

import { PromptViewTracker } from "@/components/analytics/PromptViewTracker";
import { TrackedUpgradeButton } from "@/components/analytics/TrackedUpgradeButton";
import { CopyPromptButton } from "@/components/CopyPromptButton";
import { PromptMarketplaceActions } from "@/components/PromptMarketplaceActions";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { SavePromptButton } from "@/components/SavePromptButton";
import { JsonLd } from "@/components/seo/JsonLd";
import { TokenAmount } from "@/components/ui/TokenAmount";
import {
  ApiRequestError,
  fetchCategories,
  fetchLearningCourse,
  fetchPromptBySlug,
  fetchRelatedPromptsBySlug,
} from "@/lib/api";
import { appRoute, LEARNING_FOUNDATIONS_COURSE_SLUG } from "@/lib/constants/routes";
import {
  formatTranslation,
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getTechniqueTranslationKey,
  getTranslation,
} from "@/lib/i18n";
import { isOfficialTeamContributor } from "@/lib/contributors";
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
      description: prompt.summary ?? formatTranslation(language, "prompt.metadataDescriptionFallback", { title: prompt.title }),
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
    const [categories, related, foundationsCourse] = await Promise.all([
      fetchCategories(accessToken, language),
      fetchRelatedPromptsBySlug(slug, { limit: 4, accessToken, language }).catch(() => [] as PromptListItem[]),
      fetchLearningCourse(LEARNING_FOUNDATIONS_COURSE_SLUG, accessToken, language).catch(() => null),
    ]);

    const category = categories.find((item) => item.id === prompt.category_id);
    const foundationsCourseTitle = foundationsCourse?.title ?? getTranslation(language, "learn.course");
    const foundationsCourseHref =
      foundationsCourse?.resume_href ?? appRoute.learnCourse(LEARNING_FOUNDATIONS_COURSE_SLUG);
    const isOfficialTeamAuthor = isOfficialTeamContributor(prompt.contributor_slug);
    const hasVerifiedTier = prompt.contributor_tier === "verified" || prompt.contributor_tier === "top";
    const shouldShowVerifiedBadge = isOfficialTeamAuthor || hasVerifiedTier;
    const verifiedBadgeLabel = isOfficialTeamAuthor
      ? getTranslation(language, "prompt.officialTeamBadge")
      : getTranslation(language, prompt.contributor_tier === "top" ? "contributorTier.top" : "contributorTier.verified");
    const canShowCreatorProfileLink = Boolean(prompt.contributor_slug) && !isOfficialTeamAuthor;
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

          {prompt.body_locked && !prompt.price ? (
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
                    <span>{getTranslation(language, "prompt.unlockWithLumens")}</span>
                    <TokenAmount amount={prompt.unlock_offer.price} state="spent" />
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

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
          <section className="pv-panel px-6 py-6 sm:px-7">
            <div className="relative">
              {!prompt.body_locked ? (
                <div className="absolute right-3 top-3 z-10">
                  <CopyPromptButton promptId={prompt.id} body={prompt.body} metadata={interactionMetadata} variant="icon" />
                </div>
              ) : null}
              <pre className={`overflow-x-auto whitespace-pre-wrap rounded-[1.25rem] border border-[var(--pv-border)] bg-white/80 p-5 font-mono text-sm leading-relaxed text-zinc-900 ${!prompt.body_locked ? "pr-14" : ""}`}>
                {prompt.body}
              </pre>
            </div>
          </section>

          <aside className="space-y-4">
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">
                {prompt.price ? getTranslation(language, "prompt.marketplaceAccess") : prompt.body_locked
                  ? prompt.unlock_offer
                    ? getTranslation(language, "prompt.unlockWithLumens")
                    : getTranslation(language, "prompt.upgradeToUnlock")
                  : getTranslation(language, "dashboard.tryNow")}
              </p>
              <div className="mt-4 flex flex-col gap-3">
                {!prompt.body_locked ? (
                  <a
                    href="https://t.me/prompts_souz_bot"
                    target="_blank"
                    rel="noreferrer"
                    className="pv-button-primary inline-flex items-center justify-center gap-2"
                  >
                    <TelegramIcon className="h-4 w-4" />
                    <span>{getTranslation(language, "prompt.testInTelegram")}</span>
                  </a>
                ) : null}
                {prompt.body_locked && prompt.unlock_offer ? (
                  <Link href="/store" className="pv-button-primary">
                    <span>{getTranslation(language, "prompt.unlockWithLumens")}</span>
                    <TokenAmount amount={prompt.unlock_offer.price} state="spent" />
                  </Link>
                ) : null}
                <SavePromptButton promptId={prompt.id} promptSlug={prompt.slug} metadata={interactionMetadata} />
              </div>

              {prompt.price ? (
                <div className="mt-5 border-t border-[var(--pv-border)] pt-4">
                  <PromptMarketplaceActions
                    promptId={prompt.id}
                    promptSlug={prompt.slug}
                    price={prompt.price}
                    access={prompt.access}
                    bodyLocked={Boolean(prompt.body_locked)}
                  />
                </div>
              ) : null}

              {prompt.author_display_name || prompt.author_rating_average ? (
                <div className="mt-5 border-t border-[var(--pv-border)] pt-4 text-sm text-zinc-700">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-zinc-950">
                      {prompt.author_display_name ?? getTranslation(language, "prompt.creatorFallback")}
                    </p>
                    {shouldShowVerifiedBadge ? (
                      <span
                        className="inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center bg-[#4a8df6] shadow-[0_1px_2px_rgba(15,23,42,0.18)]"
                        style={{
                          clipPath: "polygon(50% 0%, 82% 18%, 100% 50%, 82% 82%, 50% 100%, 18% 82%, 0% 50%, 18% 18%)",
                        }}
                        aria-label={verifiedBadgeLabel}
                        title={verifiedBadgeLabel}
                      >
                        <svg viewBox="0 0 20 20" className="h-3 w-3 text-white" aria-hidden="true" focusable="false">
                          <path
                            d="M5.1 10.2 8.2 13.25l6.7-6.55"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3.2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                    ) : null}
                  </div>
                  {prompt.author_rating_average ? (
                    <p className="mt-1">
                      {formatTranslation(language, "prompt.authorRatingReviews", {
                        rating: prompt.author_rating_average.toFixed(1),
                        count: prompt.author_rating_count ?? 0,
                      })}
                    </p>
                  ) : null}
                  {canShowCreatorProfileLink && prompt.contributor_slug ? (
                    <Link
                      href={`/contributors/${encodeURIComponent(prompt.contributor_slug)}`}
                      className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
                    >
                      {getTranslation(language, "prompt.creatorProfile")}
                      <span aria-hidden="true">↗</span>
                    </Link>
                  ) : null}
                </div>
              ) : null}

              <div className="mt-5 border-t border-[var(--pv-border)] pt-4">
                <p className="text-sm font-medium text-zinc-950">{foundationsCourseTitle}</p>
                <Link
                  href={foundationsCourseHref}
                  className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
                >
                  {getTranslation(language, "prompt.learnHowItWorks")}
                  <span aria-hidden="true">↗</span>
                </Link>
              </div>
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

function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" className={className} aria-hidden="true" focusable="false">
      <path d="m21.2 4.8-2.7 13.1c-.2 1-1 1.2-1.8.8l-4.2-3.1-2 1.9c-.2.2-.4.4-.8.4l.3-4.4 8.1-7.4c.4-.3-.1-.5-.6-.2l-10 6.3-4.3-1.4c-.9-.3-.9-.9.2-1.4L19.5 4c.8-.3 1.5.2 1.7.8Z" />
    </svg>
  );
}
