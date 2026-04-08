"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { findUpcomingPayout, formatDualCurrency } from "@/components/profile/presentation";
import { APP_ROUTES } from "@/lib/constants/routes";
import { formatDate } from "@/lib/formatters";
import type { BalanceCardProps } from "@/components/profile/panels/types";

export function BalanceCard({ summary, payouts, locale }: BalanceCardProps) {
  const { t } = useI18n();
  const nextPayout = findUpcomingPayout(payouts);
  const nextPayoutDate = nextPayout
    ? formatDate(nextPayout.requested_at, locale)
    : t("profile.noData");

  return (
    <div className="pv-panel p-6 sm:p-7">
      <p className="pv-kicker">{t("profile.sellerBalanceTitle")}</p>
      <p className="mt-3 text-xs uppercase tracking-[0.2em] text-zinc-500">{t("profile.availableToPayout")}</p>
      <p className="mt-2 text-[2rem] font-bold leading-tight tracking-[-0.05em] text-zinc-950 sm:text-[2.65rem]">
        {formatDualCurrency(summary.available_balance_rub, summary.available_balance_lumens, locale)}
      </p>
      <p className="mt-2 text-sm text-zinc-600">{t("profile.nextPayoutDate", { date: nextPayoutDate })}</p>
      <p className="mt-1 text-xs text-zinc-500">
        {summary.payout_eligible ? t("profile.availableToPayoutReady") : t("profile.availableToPayoutEmpty")}
      </p>
      <div className="mt-5 flex flex-wrap gap-3">
        <Link href={APP_ROUTES.wallet} className="pv-button-primary !w-auto">
          {t("profile.withdrawFunds")}
        </Link>
        <Link href={APP_ROUTES.dashboard} className="pv-button-secondary !w-auto">
          {t("profile.openReport")}
        </Link>
      </div>
    </div>
  );
}

