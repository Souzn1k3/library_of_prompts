import { humanizeSnakeCase } from "@/lib/formatters";
import type { MarketplacePayout, PromptMarketplacePurchase, PromptReview, ReviewModerationStatus } from "@/lib/types";

import type { TranslateFn } from "./presentationTypes";

const TRUST_INDICATOR_LABELS: Record<string, string> = {
  verified_creator: "profile.trustVerifiedCreator",
  top_contributor: "profile.trustTopContributor",
  high_rating: "profile.trustHighRating",
  top_seller: "profile.trustTopSeller",
  new_marketplace_profile: "profile.trustNewMarketplaceProfile",
};

const PAYMENT_METHOD_LABELS: Record<PromptMarketplacePurchase["payment_method"], string> = {
  included_limit: "profile.paymentMethodIncludedLimit",
  lumens: "profile.paymentMethodLumens",
  legacy_store: "profile.paymentMethodLegacyStore",
  stripe: "profile.paymentMethodDirectCheckout",
};

const PURCHASE_STATUS_LABELS: Record<PromptMarketplacePurchase["status"], string> = {
  pending: "profile.purchaseStatusPending",
  completed: "profile.purchaseStatusCompleted",
  failed: "profile.purchaseStatusFailed",
  canceled: "profile.purchaseStatusCanceled",
  refunded: "profile.purchaseStatusRefunded",
};

const SETTLEMENT_STATUS_LABELS: Record<Exclude<PromptMarketplacePurchase["settlement_status"], undefined>, string> = {
  pending: "profile.settlementStatusPending",
  available: "profile.settlementStatusAvailable",
  paid_out: "profile.settlementStatusPaidOut",
  refunded: "profile.settlementStatusRefunded",
  disputed: "profile.settlementStatusDisputed",
};

const PAYOUT_STATUS_LABELS: Record<MarketplacePayout["status"], string> = {
  requested: "profile.payoutStatusRequested",
  processing: "profile.payoutStatusProcessing",
  paid: "profile.payoutStatusPaid",
  failed: "profile.payoutStatusFailed",
  canceled: "profile.payoutStatusCanceled",
};

const REVIEW_MODERATION_STATUS_LABELS: Record<ReviewModerationStatus, string> = {
  visible: "profile.reviewModerationVisible",
  pending: "profile.reviewModerationPending",
  hidden: "profile.reviewModerationHidden",
};

const REVIEW_MODERATION_REASON_LABELS: Record<string, string> = {
  refunded_purchase: "profile.reviewReasonRefundedPurchase",
  reported_by_users: "profile.reviewReasonReportedByUsers",
  review_velocity: "profile.reviewReasonReviewVelocity",
  repeat_buyer_seller_pattern: "profile.reviewReasonRepeatBuyerSellerPattern",
  dense_buyer_seller_activity: "profile.reviewReasonDenseBuyerSellerActivity",
  duplicate_review_text: "profile.reviewReasonDuplicateReviewText",
};

export function humanizeTrustIndicator(key: string, t: TranslateFn): string {
  return TRUST_INDICATOR_LABELS[key] ? t(TRUST_INDICATOR_LABELS[key]) : humanizeSnakeCase(key);
}

export function humanizePaymentMethod(value: PromptMarketplacePurchase["payment_method"], t: TranslateFn): string {
  return t(PAYMENT_METHOD_LABELS[value]);
}

export function humanizePurchaseStatus(status: PromptMarketplacePurchase["status"], t: TranslateFn): string {
  return t(PURCHASE_STATUS_LABELS[status]);
}

export function humanizeSettlementStatus(status: PromptMarketplacePurchase["settlement_status"], t: TranslateFn): string {
  if (!status) {
    return t("profile.settlementStatusPending");
  }
  return t(SETTLEMENT_STATUS_LABELS[status]);
}

export function humanizePayoutStatus(status: MarketplacePayout["status"], t: TranslateFn): string {
  return t(PAYOUT_STATUS_LABELS[status]);
}

export function humanizePayoutTableStatus(status: MarketplacePayout["status"], t: TranslateFn): string {
  switch (status) {
    case "requested":
      return t("profile.payoutTableStatusProcessing");
    case "processing":
      return t("profile.payoutTableStatusSent");
    case "paid":
      return t("profile.payoutTableStatusCredited");
    case "failed":
    case "canceled":
      return t("profile.payoutTableStatusError");
    default:
      return humanizePayoutStatus(status, t);
  }
}

export function humanizePayoutMethod(currencyCode: string, t: TranslateFn): string {
  const normalized = currencyCode.toUpperCase();
  if (normalized === "RUB") {
    return t("profile.payoutMethodRub");
  }
  return t("profile.payoutMethodLmn");
}

export function humanizeReviewModerationStatus(
  status: PromptReview["moderation_status"] | null | undefined,
  t: TranslateFn,
): string {
  return t(REVIEW_MODERATION_STATUS_LABELS[status ?? "visible"]);
}

export function humanizeReviewModerationReason(reason: string, t: TranslateFn): string {
  return REVIEW_MODERATION_REASON_LABELS[reason]
    ? t(REVIEW_MODERATION_REASON_LABELS[reason])
    : humanizeSnakeCase(reason);
}
