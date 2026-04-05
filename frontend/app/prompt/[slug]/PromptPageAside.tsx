import Link from "next/link";

import { PromptMarketplaceActions } from "@/components/PromptMarketplaceActions";
import { SavePromptButton } from "@/components/SavePromptButton";
import { TokenAmount } from "@/components/ui/TokenAmount";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import type { PromptDetail } from "@/lib/types";

type PromptPageAsideProps = {
  language: Language;
  prompt: PromptDetail;
  interactionMetadata: Record<string, string | null>;
  shouldShowVerifiedBadge: boolean;
  verifiedBadgeLabel: string;
  canShowCreatorProfileLink: boolean;
  foundationsCourseTitle: string;
  foundationsCourseHref: string;
};

export function PromptPageAside({
  language,
  prompt,
  interactionMetadata,
  shouldShowVerifiedBadge,
  verifiedBadgeLabel,
  canShowCreatorProfileLink,
  foundationsCourseTitle,
  foundationsCourseHref,
}: PromptPageAsideProps) {
  return (
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
                <VerifiedContributorBadge label={verifiedBadgeLabel} />
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
  );
}

function VerifiedContributorBadge({ label }: { label: string }) {
  return (
    <span
      className="inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center bg-[#4a8df6] shadow-[0_1px_2px_rgba(15,23,42,0.18)]"
      style={{
        clipPath: "polygon(50% 0%, 82% 18%, 100% 50%, 82% 82%, 50% 100%, 18% 82%, 0% 50%, 18% 18%)",
      }}
      aria-label={label}
      title={label}
    >
      <svg
        viewBox="0 0 20 20"
        className="h-3 w-3 text-white"
        aria-hidden="true"
        focusable="false"
      >
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
  );
}

function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path d="m21.2 4.8-2.7 13.1c-.2 1-1 1.2-1.8.8l-4.2-3.1-2 1.9c-.2.2-.4.4-.8.4l.3-4.4 8.1-7.4c.4-.3-.1-.5-.6-.2l-10 6.3-4.3-1.4c-.9-.3-.9-.9.2-1.4L19.5 4c.8-.3 1.5.2 1.7.8Z" />
    </svg>
  );
}
