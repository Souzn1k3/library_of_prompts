"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  findLatestPaidPayout,
  findNearestPendingSettlementDate,
  findUpcomingPayout,
  formatDualCurrency,
  formatPaidOutLast30,
  formatPayoutAmount,
  humanizePayoutMethod,
  humanizePayoutTableStatus,
  humanizeTrustIndicator,
} from "@/components/profile/presentation";
import { APP_ROUTES } from "@/lib/constants/routes";
import { formatDate } from "@/lib/formatters";
import type { MarketplacePayout, PromptMarketplacePurchase, SellerMarketplaceSummary } from "@/lib/types";

type BalanceCardProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  locale: string;
};

type MoneyStatusBlockProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

type WhyZeroBalanceBlockProps = {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

type MoneyPipelineProps = {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
};

type PayoutsTableProps = {
  payouts: MarketplacePayout[];
  locale: string;
};

type SellerTrustBlockProps = {
  summary: SellerMarketplaceSummary;
  ratingLabel: string;
  reviewsHref: string;
  publicReviewsHref: string | null;
};

export function BalanceCard({ summary, payouts, locale }: BalanceCardProps) {
  const { t } = useI18n();
  const nextPayout = findUpcomingPayout(payouts);
  const nextPayoutDate = nextPayout ? formatDate(nextPayout.requested_at, locale) : t("profile.noData");

  return (
    <div className="rounded-[1.75rem] border border-zinc-200 bg-white p-6 shadow-[0_1px_0_rgba(0,0,0,0.04)] sm:p-7">
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

export function MoneyStatusBlock({ summary, payouts, purchases, locale }: MoneyStatusBlockProps) {
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

export function WhyZeroBalanceBlock({ summary, purchases, locale }: WhyZeroBalanceBlockProps) {
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
        ? t("profile.zeroReasonPendingWithDate", { amount: pendingAmount, date: formatDate(pendingReleaseDate, locale) })
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

export function MoneyPipeline({ summary, payouts, purchases, locale }: MoneyPipelineProps) {
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

export function PayoutsTable({ payouts, locale }: PayoutsTableProps) {
  const { t } = useI18n();
  const sortedPayouts = [...payouts].sort((left, right) => Date.parse(right.requested_at) - Date.parse(left.requested_at));
  const upcomingPayout = findUpcomingPayout(payouts) ?? sortedPayouts[0] ?? null;

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="pv-kicker">{t("profile.recentPayouts")}</p>
          <p className="mt-1 text-sm text-zinc-600">{t("profile.recentPayoutsDescription")}</p>
        </div>
      </div>
      <div className="mt-4 rounded-[1rem] border border-zinc-200 bg-white p-4">
        <p className="text-xs uppercase tracking-[0.16em] text-zinc-500">{t("profile.nextPayoutCardTitle")}</p>
        {upcomingPayout ? (
          <>
            <p className="mt-2 text-lg font-semibold text-zinc-950">{formatPayoutAmount(upcomingPayout, locale)}</p>
            <p className="mt-1 text-sm text-zinc-600">
              {t("profile.nextPayoutCardDate", { date: formatDate(upcomingPayout.requested_at, locale) })}
            </p>
            <p className="mt-1 text-sm text-zinc-600">
              {t("profile.nextPayoutCardStatus", { status: humanizePayoutTableStatus(upcomingPayout.status, t) })}
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-zinc-500">{t("profile.noData")}</p>
        )}
      </div>
      {sortedPayouts.length ? (
        <div className="mt-4 overflow-x-auto rounded-[1rem] border border-zinc-200 bg-white">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50 text-left text-xs uppercase tracking-[0.14em] text-zinc-500">
                <th className="px-4 py-3">{t("profile.payoutsDateColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsAmountColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsStatusColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsMethodColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsIdColumn")}</th>
              </tr>
            </thead>
            <tbody>
              {sortedPayouts.map((payout) => (
                <tr key={payout.id} className="border-b border-zinc-100 last:border-b-0">
                  <td className="px-4 py-3 text-zinc-700">{formatDate(payout.requested_at, locale)}</td>
                  <td className="px-4 py-3 font-medium text-zinc-900">{formatPayoutAmount(payout, locale)}</td>
                  <td className="px-4 py-3 text-zinc-700">{humanizePayoutTableStatus(payout.status, t)}</td>
                  <td className="px-4 py-3 text-zinc-600">{humanizePayoutMethod(payout.currency_code, t)}</td>
                  <td className="px-4 py-3 text-zinc-600">{payout.external_reference ?? payout.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-4 text-sm text-zinc-500">{t("profile.noPayouts")}</p>
      )}
    </div>
  );
}

export function SellerTrustBlock({ summary, ratingLabel, reviewsHref, publicReviewsHref }: SellerTrustBlockProps) {
  const { t } = useI18n();

  return (
    <div className="rounded-[1.25rem] border border-zinc-200/80 bg-zinc-50/80 p-5 text-sm text-zinc-700">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{t("profile.sellerTrustSecondaryKicker")}</p>
      <h3 className="mt-2 text-lg font-semibold text-zinc-900">{t("profile.sellerTrust")}</h3>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Link href={reviewsHref} className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-900">
          {summary.review_count > 0
            ? t("profile.ratingReviewsEntry", { rating: ratingLabel, count: summary.review_count })
            : t("profile.ratingReviewsEntryEmpty")}
        </Link>
        {publicReviewsHref ? (
          <Link href={publicReviewsHref} className="text-xs font-semibold text-[var(--pv-brand)]">
            {t("profile.openPublicReviewPage")}
          </Link>
        ) : null}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.averageRating")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{ratingLabel}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.verifiedReviews")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.review_count}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <div className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.promptsSold")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.sold_prompts_count}</p>
        </div>
      </div>
      <p className="mt-4 text-xs text-zinc-500">{t("profile.sellerTrustDescription")}</p>
      {summary.trust_indicators.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {summary.trust_indicators.map((indicator) => (
            <span key={indicator.key} className="pv-chip">
              {humanizeTrustIndicator(indicator.key, t)}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function StatusMetric({ title, value, caption }: { title: string; value: string; caption?: string }) {
  return (
    <div className="rounded-[1rem] border border-zinc-200/80 bg-white p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{title}</p>
      <p className="mt-2 text-sm font-semibold text-zinc-900">{value}</p>
      {caption ? <p className="mt-1 text-xs text-zinc-500">{caption}</p> : null}
    </div>
  );
}
