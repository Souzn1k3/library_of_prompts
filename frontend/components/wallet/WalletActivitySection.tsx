"use client";

import { LmnAmount } from "@/components/ui/LmnAmount";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDateTime } from "@/lib/formatters";
import type { CurrencyTransaction } from "@/lib/types";
import {
  formatSignedAmount,
  reasonLabel,
  type WalletTranslate,
} from "@/components/wallet/walletPresentation";

type WalletActivitySectionProps = {
  balance: number;
  allTransactions: CurrencyTransaction[];
  pagedTransactions: CurrencyTransaction[];
  activityPageSize: number;
  currentActivityPage: number;
  totalActivityPages: number;
  onPreviousPage: () => void;
  onNextPage: () => void;
  locale: string;
  t: WalletTranslate;
};

export function WalletActivitySection({
  balance,
  allTransactions,
  pagedTransactions,
  activityPageSize,
  currentActivityPage,
  totalActivityPages,
  onPreviousPage,
  onNextPage,
  locale,
  t,
}: WalletActivitySectionProps) {
  return (
    <section className="pv-panel px-5 py-5">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker">{t("wallet.operationsTimeline")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("wallet.operationsTimeline")}
          </h2>
        </div>
        <LmnAmount amount={balance} symbol={TOKEN_SHORT_CODE} state="balance" />
      </div>

      {allTransactions.length === 0 ? (
        <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.empty")}</div>
      ) : (
        <div className="mt-5 space-y-3">
          {pagedTransactions.map((transaction) => (
            <div key={transaction.id} className="pv-card-muted p-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span
                    className={`mt-1 h-2.5 w-2.5 rounded-full ${
                      transaction.amount > 0 ? "bg-[var(--pv-success)]" : "bg-slate-400"
                    }`}
                  />
                  <div>
                    <p className="font-semibold text-zinc-900">
                      {reasonLabel(transaction.reason, t)}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {formatDateTime(transaction.created_at, locale)}
                      {transaction.context ? ` · ${transaction.context}` : ""}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <LmnAmount
                    amount={formatSignedAmount(transaction.amount)}
                    symbol={TOKEN_SHORT_CODE}
                    state={transaction.amount > 0 ? "earned" : "spent"}
                    className="pv-lmn-token-no-border"
                  />
                  <p className="mt-2 text-xs text-zinc-500">
                    {t("wallet.balance")}: {transaction.balance_after}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {allTransactions.length > activityPageSize ? (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={onPreviousPage}
            disabled={currentActivityPage <= 1}
            className="pv-button-secondary !w-auto disabled:opacity-60"
          >
            {t("wallet.prevPage")}
          </button>
          <p className="text-sm text-zinc-600">
            {t("wallet.pageCounter", { current: currentActivityPage, total: totalActivityPages })}
          </p>
          <button
            type="button"
            onClick={onNextPage}
            disabled={currentActivityPage >= totalActivityPages}
            className="pv-button-secondary !w-auto disabled:opacity-60"
          >
            {t("wallet.nextPage")}
          </button>
        </div>
      ) : null}
    </section>
  );
}
