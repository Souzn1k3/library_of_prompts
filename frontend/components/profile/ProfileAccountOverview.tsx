"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { humanizeTrustIndicator, renderRating } from "@/components/profile/presentation";
import { appRoute } from "@/lib/constants/routes";
import { formatDate } from "@/lib/formatters";
import type { SellerMarketplaceSummary, UserProfile } from "@/lib/types";

type ProfileTranslate = (key: string, params?: Record<string, string | number | null | undefined>) => string;

type ProfileAccountOverviewProps = {
  user: UserProfile;
  summary: SellerMarketplaceSummary;
  ratingLabel: string;
  locale: string;
  t: ProfileTranslate;
};

export function ProfileAccountOverview({
  user,
  summary,
  ratingLabel,
  locale,
  t,
}: ProfileAccountOverviewProps) {
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <p className="pv-kicker">{t("profile.accountTitle")}</p>
      <h2 className="mt-3 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
        {user.display_name}
      </h2>
      <dl className="mt-6 grid gap-4 sm:grid-cols-2">
        <MetricCard label={t("profile.emailLabel")}>
          <p className="mt-3 font-medium text-zinc-900">{user.email}</p>
        </MetricCard>
        <MetricCard label={t("profile.memberSince")}>
          <p className="mt-3 font-medium text-zinc-900">{formatDate(user.created_at, locale)}</p>
        </MetricCard>
        <MetricCard label={t("profile.creatorRating")}>
          <p className="mt-3 font-medium text-zinc-900">
            {renderRating(summary.rating_display, t("profile.noReviewsYet"))}
          </p>
          <p className="mt-2 text-sm text-zinc-600">
            {ratingLabel} · {t("profile.reviewCountLabel", { count: summary.review_count })}
          </p>
          {user.contributor_slug ? (
            <Link
              href={appRoute.contributorBySlugReviewSort(user.contributor_slug, "best")}
              className="mt-2 inline-flex text-xs font-semibold text-[var(--pv-brand-strong)]"
            >
              {t("profile.openPublicReviewPage")}
            </Link>
          ) : null}
        </MetricCard>
        <MetricCard label={t("profile.marketplaceSummary")}>
          <p className="mt-3 font-medium text-zinc-900">
            {t("profile.soldPromptsLabel", { count: summary.sold_prompts_count })}
          </p>
          <p className="mt-2 text-sm text-zinc-600">
            {t("profile.buyerPurchasesLabel", { count: summary.purchases_count })}
          </p>
        </MetricCard>
      </dl>

      {summary.trust_indicators.length ? (
        <div className="mt-5 flex flex-wrap gap-2">
          {summary.trust_indicators.map((indicator) => (
            <span
              key={indicator.key}
              className={indicator.level === "strong" ? "pv-badge-warning" : "pv-chip"}
            >
              {humanizeTrustIndicator(indicator.key, t)}
            </span>
          ))}
        </div>
      ) : null}

      {user.contributor_slug ? (
        <Link
          href={appRoute.contributorBySlug(user.contributor_slug)}
          className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]"
        >
          {t("profile.publicCreatorProfile")}
          <span aria-hidden="true">↗</span>
        </Link>
      ) : null}
    </section>
  );
}

function MetricCard({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/75 p-4">
      <dt className="pv-kicker">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
