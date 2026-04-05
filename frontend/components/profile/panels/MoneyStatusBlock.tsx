"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  findNearestPendingSettlementDate,
  formatDualCurrency,
  formatPaidOutLast30,
} from "@/components/profile/presentation";
import { formatDate } from "@/lib/formatters";
import { StatusMetric } from "@/components/profile/panels/StatusMetric";
import type { MoneyStatusBlockProps } from "@/components/profile/panels/types";

export function MoneyStatusBlock({
  summary,
  payouts,
  purchases,
  locale,
}: MoneyStatusBlockProps) {
  const { t } = useI18n();
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);
  const pendingReleaseLabel = pendingReleaseDate
    ? t("profile.pendingReleaseAt", { date: formatDate(pendingReleaseDate, locale) })
    : t("profile.pendingReleaseNoDate");
  const holdRub = summary.clawback_due_rub + summary.disputed_balance_rub;
  const holdLumens = summary.clawback_due_lumens + summary.disputed_balance_lumens;
  const paidOutLast30 = formatPaidOutLast30(payouts, locale, t);

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <p className="pv-kicker">{t("profile.moneyStatusTitle")}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <StatusMetric
          title={t("profile.pendingStatus")}
          value={formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale)}
          caption={pendingReleaseLabel}
        />
        <StatusMetric
          title={t("profile.fees")}
          value={formatDualCurrency(summary.platform_commission_rub, summary.platform_commission_lumens, locale)}
        />
        <StatusMetric
          title={t("profile.holdsAndDisputes")}
          value={formatDualCurrency(holdRub, holdLumens, locale)}
          caption={`${t("profile.refunded")}: ${formatDualCurrency(summary.refunded_balance_rub, summary.refunded_balance_lumens, locale)}`}
        />
        <StatusMetric
          title={t("profile.paidOutLast30")}
          value={paidOutLast30.value}
          caption={paidOutLast30.caption}
        />
      </div>
    </div>
  );
}

