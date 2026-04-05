"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  findNearestPendingSettlementDate,
  formatDualCurrency,
} from "@/components/profile/presentation";
import { formatDate } from "@/lib/formatters";
import type { WhyZeroBalanceBlockProps } from "@/components/profile/panels/types";

export function WhyZeroBalanceBlock({
  summary,
  purchases,
  locale,
}: WhyZeroBalanceBlockProps) {
  const { t } = useI18n();
  const hasZeroAvailable = summary.available_balance_rub === 0 && summary.available_balance_lumens === 0;
  if (!hasZeroAvailable) {
    return null;
  }

  const reasons: string[] = [];
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);

  if (summary.pending_balance_rub !== 0 || summary.pending_balance_lumens !== 0) {
    const pendingAmount = formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale);
    reasons.push(
      pendingReleaseDate
        ? t("profile.zeroReasonPendingWithDate", {
            amount: pendingAmount,
            date: formatDate(pendingReleaseDate, locale),
          })
        : t("profile.zeroReasonPendingNoDate", { amount: pendingAmount }),
    );
  }

  const holdRub = summary.clawback_due_rub + summary.disputed_balance_rub;
  const holdLumens = summary.clawback_due_lumens + summary.disputed_balance_lumens;
  if (holdRub !== 0 || holdLumens !== 0) {
    reasons.push(t("profile.zeroReasonHoldDispute", { amount: formatDualCurrency(holdRub, holdLumens, locale) }));
  }

  if ((summary.platform_commission_rub !== 0 || summary.platform_commission_lumens !== 0) && reasons.length < 3) {
    reasons.push(
      t("profile.zeroReasonCommission", {
        amount: formatDualCurrency(summary.platform_commission_rub, summary.platform_commission_lumens, locale),
      }),
    );
  }

  const hasNoSales = summary.seller_revenue_rub === 0 && summary.seller_lumens_earned === 0;
  if (hasNoSales && reasons.length < 3) {
    reasons.push(t("profile.zeroReasonNoSales"));
  }

  if (reasons.length === 0) {
    reasons.push(t("profile.zeroReasonFallback"));
  }
  reasons.push(t("profile.zeroReasonPayoutRule"));

  return (
    <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-900">
      <p className="font-semibold">{t("profile.whyZeroBalance")}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        {reasons.map((reason, index) => (
          <li key={`${reason}-${index}`}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

