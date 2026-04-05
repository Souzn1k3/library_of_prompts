"use client";

import { useMemo } from "react";

import { buildProfileSummary } from "@/components/profile/buildProfileSummary";
import { appRoute } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";
import type {
  BillingStatus,
  MarketplaceOverview,
  SellerMarketplaceSummary,
  UserProfile,
} from "@/lib/types";

type TranslateFn = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type UseProfileViewModelArgs = {
  user: UserProfile | null;
  overview: MarketplaceOverview | null;
  billing: BillingStatus | null;
  t: TranslateFn;
};

const EMPTY_SUMMARY: SellerMarketplaceSummary = {
  rating_average: null,
  rating_display: null,
  review_count: 0,
  sold_prompts_count: 0,
  purchases_count: 0,
  seller_revenue_rub: 0,
  seller_lumens_earned: 0,
  pending_balance_rub: 0,
  available_balance_rub: 0,
  paid_out_rub: 0,
  refunded_balance_rub: 0,
  disputed_balance_rub: 0,
  pending_balance_lumens: 0,
  available_balance_lumens: 0,
  paid_out_lumens: 0,
  refunded_balance_lumens: 0,
  disputed_balance_lumens: 0,
  platform_commission_rub: 0,
  platform_commission_lumens: 0,
  clawback_due_rub: 0,
  clawback_due_lumens: 0,
  payout_eligible: false,
  trust_indicators: [],
  recent_reviews: [],
  recent_payouts: [],
};

export function useProfileViewModel({
  user,
  overview,
  billing,
  t,
}: UseProfileViewModelArgs) {
  const summary = useMemo(
    () => (user ? buildProfileSummary(user, overview) : EMPTY_SUMMARY),
    [overview, user],
  );

  const payouts = useMemo(
    () => (overview?.payouts?.length ? overview.payouts : summary.recent_payouts),
    [overview?.payouts, summary.recent_payouts],
  );

  const purchases = useMemo(() => overview?.purchases ?? [], [overview?.purchases]);
  const reviews = useMemo(() => overview?.reviews ?? [], [overview?.reviews]);

  const ratingLabel = useMemo(
    () =>
      summary.rating_display ? `${summary.rating_display.toFixed(1)}/5` : t("profile.ratingNew"),
    [summary.rating_display, t],
  );

  const publicReviewsHref = useMemo(
    () => (user?.contributor_slug ? appRoute.contributorBySlugReviewSort(user.contributor_slug, "best") : null),
    [user?.contributor_slug],
  );

  const planUnlocks = useMemo(
    () =>
      billing && billing.paid_prompt_limit_total > 0
        ? `${billing.paid_prompt_limit_remaining}/${billing.paid_prompt_limit_total}`
        : "0/0",
    [billing],
  );

  return {
    summary,
    payouts,
    purchases,
    reviews,
    ratingLabel,
    publicReviewsHref,
    reviewsAnchorHref: "#seller-reviews",
    planUnlocks,
  };
}
