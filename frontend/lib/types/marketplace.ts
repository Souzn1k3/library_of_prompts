import type { PurchaseStatus } from "./economy";
import type { TrustIndicator } from "./shared";

export type ReviewSort = "new" | "best";
export type ReviewModerationStatus = "visible" | "pending" | "hidden";
export type MarketplaceSettlementStatus = "pending" | "available" | "paid_out" | "refunded" | "disputed";
export type MarketplacePayoutStatus = "requested" | "processing" | "paid" | "failed" | "canceled";

export type PromptReview = {
  id: string;
  rating: number;
  text: string | null;
  author_user_id: string;
  author_display_name: string;
  author_slug: string | null;
  prompt_id: string;
  prompt_slug: string;
  prompt_title: string;
  created_at: string;
  updated_at: string;
  verified_purchase: boolean;
  moderation_status?: ReviewModerationStatus;
  moderation_reason?: string | null;
  reported_count?: number;
};

export type PromptReviewList = {
  seller_user_id?: string | null;
  rating_average?: number | null;
  rating_display?: number | null;
  review_count: number;
  sort: ReviewSort;
  items: PromptReview[];
};

export type PromptMarketplacePurchase = {
  id: string;
  prompt_id: string;
  prompt_slug: string;
  prompt_title: string;
  seller_user_id: string | null;
  status: PurchaseStatus;
  payment_method: "included_limit" | "lumens" | "stripe" | "legacy_store";
  price_rub: number;
  price_lumens: number;
  settlement_status?: MarketplaceSettlementStatus;
  settlement_available_at?: string | null;
  paid_out_at?: string | null;
  created_at: string;
  completed_at: string | null;
  can_review: boolean;
  review?: PromptReview | null;
};

export type MarketplacePayout = {
  id: string;
  currency_code: string;
  status: MarketplacePayoutStatus;
  total_amount: number;
  purchase_count: number;
  external_reference?: string | null;
  requested_at: string;
  paid_at?: string | null;
};

export type SellerMarketplaceSummary = {
  rating_average: number | null;
  rating_display: number | null;
  review_count: number;
  sold_prompts_count: number;
  purchases_count: number;
  seller_revenue_rub: number;
  seller_lumens_earned: number;
  pending_balance_rub: number;
  available_balance_rub: number;
  paid_out_rub: number;
  refunded_balance_rub: number;
  disputed_balance_rub: number;
  pending_balance_lumens: number;
  available_balance_lumens: number;
  paid_out_lumens: number;
  refunded_balance_lumens: number;
  disputed_balance_lumens: number;
  platform_commission_rub: number;
  platform_commission_lumens: number;
  clawback_due_rub: number;
  clawback_due_lumens: number;
  payout_eligible: boolean;
  trust_indicators: TrustIndicator[];
  recent_reviews: PromptReview[];
  recent_payouts: MarketplacePayout[];
};

export type MarketplaceOverview = {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  reviews: PromptReview[];
  payouts: MarketplacePayout[];
};
