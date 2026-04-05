"use client";

import {
  BalanceCard,
  MoneyPipeline,
  MoneyStatusBlock,
  PayoutsTable,
  WhyZeroBalanceBlock,
} from "@/components/profile/MarketplacePanels";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { formatDateTime } from "@/components/profile/presentation";
import type {
  MarketplacePayout,
  PromptMarketplacePurchase,
  SellerMarketplaceSummary,
} from "@/lib/types";

type ProfileMarketplaceSectionProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
  lastMarketplaceSyncAt: string | null;
  onReload: () => void;
};

export function ProfileMarketplaceSection({
  summary,
  payouts,
  purchases,
  locale,
  lastMarketplaceSyncAt,
  onReload,
}: ProfileMarketplaceSectionProps) {
  const { t } = useI18n();

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="pv-kicker">{t("profile.marketplaceKicker")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("profile.marketplaceTitle")}
          </h2>
          <p className="mt-2 text-sm text-zinc-600">{t("profile.marketplaceDescription")}</p>
        </div>
        <div className="rounded-[1rem] border border-zinc-200 bg-white/80 px-4 py-3 text-sm text-zinc-700">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">
            {t("profile.statusHintBadge")}
          </p>
          <p className="mt-1 font-medium text-zinc-950">
            {summary.payout_eligible
              ? t("profile.payoutEligible")
              : t("profile.settlementInProgress")}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            {summary.payout_eligible
              ? t("profile.payoutEligibleDescription")
              : t("profile.settlementInProgressDescription")}
          </p>
          <p className="mt-2 text-[11px] text-zinc-500">{t("profile.statusHintNote")}</p>
        </div>
      </div>

      <div className="mt-4 rounded-[1rem] border border-zinc-200 bg-white/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
              {t("profile.marketplaceSyncTitle")}
            </p>
            <p className="mt-1 text-sm text-zinc-700">{t("profile.marketplaceSyncDescription")}</p>
            <p className="mt-2 text-xs text-zinc-500">
              {lastMarketplaceSyncAt
                ? t("profile.marketplaceSyncUpdatedAt", {
                    date: formatDateTime(lastMarketplaceSyncAt, locale),
                  })
                : t("profile.marketplaceSyncNever")}
            </p>
          </div>
          <button type="button" onClick={onReload} className="pv-button-secondary !w-auto">
            {t("profile.marketplaceSyncAction")}
          </button>
        </div>
      </div>

      <div className="mt-6 space-y-5">
        <BalanceCard summary={summary} payouts={payouts} locale={locale} />
        <MoneyStatusBlock summary={summary} payouts={payouts} purchases={purchases} locale={locale} />
        <WhyZeroBalanceBlock summary={summary} purchases={purchases} locale={locale} />
        <MoneyPipeline summary={summary} payouts={payouts} purchases={purchases} locale={locale} />
        <PayoutsTable payouts={payouts} locale={locale} />
      </div>
    </section>
  );
}
