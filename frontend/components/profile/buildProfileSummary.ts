import type {
  MarketplaceOverview,
  SellerMarketplaceSummary,
  UserProfile,
} from "@/lib/types";

export function buildProfileSummary(
  user: UserProfile,
  overview: MarketplaceOverview | null,
): SellerMarketplaceSummary {
  if (overview?.summary) {
    return overview.summary;
  }

  return {
    rating_average: user.rating_average ?? null,
    rating_display: user.rating_display ?? null,
    review_count: user.review_count ?? 0,
    sold_prompts_count: user.sold_prompts_count ?? 0,
    purchases_count: user.purchases_count ?? 0,
    seller_revenue_rub: user.seller_revenue_rub ?? 0,
    seller_lumens_earned: user.seller_lumens_earned ?? 0,
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
    trust_indicators: user.trust_indicators ?? [],
    recent_reviews: [],
    recent_payouts: [],
  };
}
