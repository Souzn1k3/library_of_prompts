"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import { languageToIntlLocale } from "@/lib/i18n";
import type { StoreItem } from "@/lib/types";

type BestNextPurchaseProps = {
  bestItem: StoreItem | null;
  balance: number;
  estimatedDaysToAfford: number | null;
};

export function BestNextPurchase({ bestItem, balance, estimatedDaysToAfford }: BestNextPurchaseProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);

  if (!bestItem) {
    return (
      <section className="pv-panel px-5 py-5">
        <p className="pv-kicker">{t("wallet.nextSpend")}</p>
        <div className="pv-empty-state mt-4 text-sm text-zinc-600">{t("store.empty")}</div>
      </section>
    );
  }

  const missing = Math.max(bestItem.price - balance, 0);
  const progressPercent = Math.max(
    8,
    Math.min(100, Math.round((Math.min(balance, bestItem.price) / Math.max(1, bestItem.price)) * 100)),
  );
  const remainingLabel = bestItem.is_affordable
    ? t("store.availableNow")
    : t("store.remaining", { count: bestItem.remaining_lumens });
  const forecastLabel =
    !bestItem.is_affordable && estimatedDaysToAfford && estimatedDaysToAfford > 0
      ? estimateLabel(language, estimatedDaysToAfford)
      : null;

  return (
    <section className="pv-panel px-5 py-5">
      <div className="pv-wallet-best-next-head flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="pv-kicker">{t("wallet.nextSpend")}</p>
          <h2 className="mt-2 text-xl font-bold tracking-[-0.04em] text-zinc-950">{bestItem.title}</h2>
        </div>
        <LmnAmount
          amount={bestItem.price}
          symbol={TOKEN_SHORT_CODE}
          strong
          state="spent"
          className="pv-wallet-best-next-price"
        />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <MetricCell
          label={t("wallet.balance")}
          value={`${formatNumber(balance, locale)} ${TOKEN_SHORT_CODE}`}
          tone="positive"
        />
        <MetricCell
          label={missingLabel(language)}
          value={`${formatNumber(missing, locale)} ${TOKEN_SHORT_CODE}`}
          tone={missing === 0 ? "positive" : "neutral"}
        />
      </div>

      <div className="mt-4 rounded-xl border border-[rgba(15,23,42,0.08)] bg-zinc-50/70 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-medium text-zinc-600">
          <span>{remainingLabel}</span>
          {forecastLabel ? <span>{forecastLabel}</span> : null}
        </div>
        <div className="mt-3 pv-progress">
          <div className="pv-progress-fill" style={{ width: `${progressPercent}%` }} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href={bestItem.is_affordable ? APP_ROUTES.store : APP_ROUTES.missions}
          className="pv-button-primary"
        >
          {bestItem.is_affordable ? t("wallet.spendNowCta") : t("wallet.earnToUnlockCta")}
        </Link>
      </div>
    </section>
  );
}

function MetricCell({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "neutral" | "positive";
}) {
  return (
    <div
      className={`rounded-xl border p-3 ${
        tone === "positive"
          ? "border-emerald-200/80 bg-emerald-50/65"
          : "border-[rgba(15,23,42,0.08)] bg-white/80"
      }`}
    >
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">{label}</p>
      <p className="mt-2 text-base font-semibold tracking-[-0.02em] text-zinc-950">{value}</p>
    </div>
  );
}

function missingLabel(language: string): string {
  if (language === "ru") {
    return "Не хватает";
  }
  if (language === "tt") {
    return "Җитми";
  }
  return "Missing";
}

function estimateLabel(language: string, days: number): string {
  if (language === "ru") {
    return `Доступно через ~${days} дн`;
  }
  if (language === "tt") {
    return `~${days} көннән соң`;
  }
  return `Available in ~${days}d`;
}
