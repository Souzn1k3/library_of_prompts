"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { renderRating } from "@/components/profile/presentation";
import { formatDate } from "@/lib/formatters";
import type { PromptReview } from "@/lib/types";

type ProfileReviewsSectionProps = {
  reviews: PromptReview[];
  publicReviewsHref: string | null;
  locale: string;
};

export function ProfileReviewsSection({
  reviews,
  publicReviewsHref,
  locale,
}: ProfileReviewsSectionProps) {
  const { t } = useI18n();

  return (
    <section id="seller-reviews" className="pv-panel px-6 py-6 sm:px-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="pv-kicker">{t("profile.recentReviews")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("profile.recentReviewsTitle")}
          </h2>
          <p className="mt-2 text-sm text-zinc-600">{t("profile.recentReviewsDescription")}</p>
        </div>
        {publicReviewsHref ? (
          <Link href={publicReviewsHref} className="text-sm font-semibold text-[var(--pv-brand)]">
            {t("profile.openPublicReviewPage")}
          </Link>
        ) : null}
      </div>

      {reviews.length ? (
        <div className="mt-6 space-y-3">
          {reviews.map((review) => (
            <div key={review.id} className="rounded-[1rem] border border-zinc-200 bg-white/75 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-zinc-900">{review.author_display_name}</p>
                  <p className="mt-1 text-xs text-zinc-500">{review.prompt_title}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-zinc-900">
                    {renderRating(review.rating, t("profile.noReviewsYet"))}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">{formatDate(review.created_at, locale)}</p>
                </div>
              </div>
              {review.text ? <p className="mt-3 text-sm text-zinc-700">{review.text}</p> : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-6 text-sm text-zinc-500">{t("profile.noBuyerReviews")}</p>
      )}
    </section>
  );
}
