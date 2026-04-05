import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import type { MarketplacePayout } from "@/lib/types";

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
