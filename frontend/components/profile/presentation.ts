import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber, humanizeSnakeCase } from "@/lib/formatters";
import type { MarketplacePayout, PromptMarketplacePurchase, PromptReview, ReviewModerationStatus } from "@/lib/types";

export type TranslateFn = (key: string, params?: Record<string, string | number | null | undefined>) => string;

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

export function formatPaidOutLast30(
  payouts: MarketplacePayout[],
  locale: string,
  t: TranslateFn,
): { value: string; caption: string | undefined } {
  if (payouts.length === 0) {
    return {
      value: `${formatNumber(0, locale)} RUB`,
      caption: t("profile.paidOutLast30NoCompleted"),
    };
  }

  const now = Date.now();
  const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000;
  const totalsByCurrency = new Map<string, number>();

  for (const payout of payouts) {
    if (payout.status !== "paid") {
      continue;
    }
    const referenceDate = payout.paid_at ?? payout.requested_at;
    const timestamp = Date.parse(referenceDate);
    if (!Number.isFinite(timestamp) || now - timestamp > thirtyDaysMs) {
      continue;
    }
    const code = payout.currency_code.toUpperCase();
    totalsByCurrency.set(code, (totalsByCurrency.get(code) ?? 0) + payout.total_amount);
  }

  if (totalsByCurrency.size === 0) {
    const fallbackCurrency = payouts[0]?.currency_code?.toUpperCase() ?? "RUB";
    return {
      value: `${formatNumber(0, locale)} ${fallbackCurrency}`,
      caption: t("profile.paidOutLast30NoCompleted"),
    };
  }

  const value = [...totalsByCurrency.entries()]
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([currency, amount]) => `${formatNumber(amount, locale)} ${currency}`)
    .join(" · ");
  return { value, caption: undefined };
}

export function findUpcomingPayout(payouts: MarketplacePayout[]): MarketplacePayout | null {
  const activeStatuses: MarketplacePayout["status"][] = ["requested", "processing"];
  const active = payouts.filter((payout) => activeStatuses.includes(payout.status));
  if (!active.length) {
    return null;
  }
  return [...active].sort((left, right) => Date.parse(left.requested_at) - Date.parse(right.requested_at))[0] ?? null;
}

export function findLatestPaidPayout(payouts: MarketplacePayout[]): MarketplacePayout | null {
  const paid = payouts.filter((payout) => payout.status === "paid" && payout.paid_at);
  if (!paid.length) {
    return null;
  }
  return [...paid].sort((left, right) => Date.parse(right.paid_at ?? right.requested_at) - Date.parse(left.paid_at ?? left.requested_at))[0] ?? null;
}

export function findNearestPendingSettlementDate(purchases: PromptMarketplacePurchase[]): string | null {
  const withDate = purchases
    .filter((purchase) => purchase.settlement_status === "pending" && purchase.settlement_available_at)
    .map((purchase) => ({
      date: purchase.settlement_available_at as string,
      timestamp: Date.parse(purchase.settlement_available_at as string),
    }))
    .filter((value) => Number.isFinite(value.timestamp))
    .sort((left, right) => left.timestamp - right.timestamp);
  if (!withDate.length) {
    return null;
  }
  return withDate[0].date;
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

export function renderRating(value: number | null | undefined, emptyLabel: string): string {
  if (!value) {
    return emptyLabel;
  }
  const rounded = Math.max(1, Math.min(5, Math.round(value)));
  return `${"★".repeat(rounded)}${"☆".repeat(5 - rounded)} ${value.toFixed(1)}`;
}

export function formatDualCurrency(rub: number, lumens: number, locale: string): string {
  const parts: string[] = [];
  if (rub !== 0 || (rub === 0 && lumens === 0)) {
    parts.push(`${formatNumber(rub, locale)} RUB`);
  }
  if (lumens !== 0) {
    parts.push(`${formatNumber(lumens, locale)} ${TOKEN_SHORT_CODE}`);
  }
  return parts.join(" · ");
}

export function formatPayoutAmount(payout: MarketplacePayout, locale: string): string {
  const code = payout.currency_code.toUpperCase() === "RUB" ? "RUB" : TOKEN_SHORT_CODE;
  return `${formatNumber(payout.total_amount, locale)} ${code}`;
}

export function formatDateTime(value: string, locale: string): string {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(parsed));
}
