"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { humanizeTrustIndicator } from "@/components/profile/presentation";
import type { SellerTrustBlockProps } from "@/components/profile/panels/types";

export function SellerTrustBlock({
  summary,
  ratingLabel,
  reviewsHref,
  publicReviewsHref,
}: SellerTrustBlockProps) {
  const { t } = useI18n();

  return (
    <div className="rounded-[1.25rem] border border-zinc-200/80 bg-zinc-50/80 p-5 text-sm text-zinc-700">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{t("profile.sellerTrustSecondaryKicker")}</p>
      <h3 className="mt-2 text-lg font-semibold text-zinc-900">{t("profile.sellerTrust")}</h3>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Link href={reviewsHref} className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-900">
          {summary.review_count > 0
            ? t("profile.ratingReviewsEntry", { rating: ratingLabel, count: summary.review_count })
            : t("profile.ratingReviewsEntryEmpty")}
        </Link>
        {publicReviewsHref ? (
          <Link href={publicReviewsHref} className="text-xs font-semibold text-[var(--pv-brand)]">
            {t("profile.openPublicReviewPage")}
          </Link>
        ) : null}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.averageRating")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{ratingLabel}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.verifiedReviews")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.review_count}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <div className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.promptsSold")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.sold_prompts_count}</p>
        </div>
      </div>
      <p className="mt-4 text-xs text-zinc-500">{t("profile.sellerTrustDescription")}</p>
      {summary.trust_indicators.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {summary.trust_indicators.map((indicator) => (
            <span key={indicator.key} className="pv-chip">
              {humanizeTrustIndicator(indicator.key, t)}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

