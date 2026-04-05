"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  findLatestPaidPayout,
  findNearestPendingSettlementDate,
  findUpcomingPayout,
  formatDualCurrency,
  formatPayoutAmount,
} from "@/components/profile/presentation";
import { formatDate } from "@/lib/formatters";
import type { MoneyPipelineProps } from "@/components/profile/panels/types";

export function MoneyPipeline({
  summary,
  payouts,
  purchases,
  locale,
}: MoneyPipelineProps) {
  const { t } = useI18n();
  const upcomingPayout = findUpcomingPayout(payouts);
  const latestPaidPayout = findLatestPaidPayout(payouts);
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);

  const steps: Array<{ label: string; amount: string; date?: string }> = [
    {
      label: t("profile.pipelinePaidByBuyers"),
      amount: formatDualCurrency(summary.seller_revenue_rub, summary.seller_lumens_earned, locale),
    },
    {
      label: t("profile.pipelineInHold"),
      amount: formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale),
      date: pendingReleaseDate ? formatDate(pendingReleaseDate, locale) : undefined,
    },
    {
      label: t("profile.pipelineAvailable"),
      amount: formatDualCurrency(summary.available_balance_rub, summary.available_balance_lumens, locale),
    },
    {
      label: t("profile.pipelinePayout"),
      amount: upcomingPayout ? formatPayoutAmount(upcomingPayout, locale) : t("profile.pipelineNoPayoutQueue"),
      date: upcomingPayout ? formatDate(upcomingPayout.requested_at, locale) : undefined,
    },
    {
      label: t("profile.pipelinePaidOut"),
      amount: formatDualCurrency(summary.paid_out_rub, summary.paid_out_lumens, locale),
      date: latestPaidPayout?.paid_at ? formatDate(latestPaidPayout.paid_at, locale) : undefined,
    },
  ];

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <p className="pv-kicker">{t("profile.moneyPipelineTitle")}</p>
      <ol className="mt-4 space-y-3">
        {steps.map((step, index) => (
          <li key={`${step.label}-${index}`} className="relative rounded-[1rem] border border-zinc-200/80 bg-white p-3 pl-10">
            <span className="absolute left-4 top-4 h-2.5 w-2.5 rounded-full bg-[var(--pv-brand)]" aria-hidden="true" />
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{step.label}</p>
            <p className="mt-1 text-sm font-semibold text-zinc-900">{step.amount}</p>
            {step.date ? <p className="mt-1 text-xs text-zinc-500">{t("profile.pipelineDate", { date: step.date })}</p> : null}
          </li>
        ))}
      </ol>
    </div>
  );
}

