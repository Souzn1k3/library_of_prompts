import { formatNumber } from "@/lib/formatters";
import type { MarketplacePayout, PromptMarketplacePurchase } from "@/lib/types";

import type { TranslateFn } from "./presentationTypes";

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
