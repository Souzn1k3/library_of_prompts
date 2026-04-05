import type {
  MarketplacePayout,
  PromptMarketplacePurchase,
  SellerMarketplaceSummary,
} from "@/lib/types";

export type BalanceCardProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  locale: string;
};

export type MoneyStatusBlockProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

export type WhyZeroBalanceBlockProps = {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

export type MoneyPipelineProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

export type PayoutsTableProps = {
  payouts: MarketplacePayout[];
  locale: string;
};

export type SellerTrustBlockProps = {
  summary: SellerMarketplaceSummary;
  ratingLabel: string;
  reviewsHref: string;
  publicReviewsHref: string | null;
};

