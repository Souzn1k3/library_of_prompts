"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  findUpcomingPayout,
  formatPayoutAmount,
  humanizePayoutMethod,
  humanizePayoutTableStatus,
} from "@/components/profile/presentation";
import { formatDate } from "@/lib/formatters";
import type { PayoutsTableProps } from "@/components/profile/panels/types";

export function PayoutsTable({ payouts, locale }: PayoutsTableProps) {
  const { t } = useI18n();
  const sortedPayouts = [...payouts].sort(
    (left, right) => Date.parse(right.requested_at) - Date.parse(left.requested_at),
  );
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
              {t("profile.nextPayoutCardStatus", {
                status: humanizePayoutTableStatus(upcomingPayout.status, t),
              })}
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

