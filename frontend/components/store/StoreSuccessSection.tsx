"use client";

import { LmnAmount } from "@/components/ui/LmnAmount";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import type { PurchaseResult } from "@/lib/types";
import type { TranslateFn } from "@/components/store/presentation";

type StoreSuccessSectionProps = {
  success: PurchaseResult;
  successPurchaseItemTitle: string | null;
  successRewardCopy: { title: string | null; body: string | null } | null;
  successDiscountCode: string | null;
  t: TranslateFn;
};

export function StoreSuccessSection({
  success,
  successPurchaseItemTitle,
  successRewardCopy,
  successDiscountCode,
  t,
}: StoreSuccessSectionProps) {
  return (
    <section className="space-y-3">
      <div className="pv-alert pv-alert-success flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">
            {t("store.purchased")}: {successPurchaseItemTitle ?? success.purchase.item.title}
          </p>
          <p className="mt-1 text-sm text-emerald-900/80">
            {t("store.purchaseSummarySpent", {
              amount: success.purchase.price_paid,
              symbol: TOKEN_SHORT_CODE,
            })}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <LmnAmount amount={`-${success.purchase.price_paid}`} symbol={TOKEN_SHORT_CODE} state="spent" />
          <span className="pv-chip">
            {t("store.currentBalance", {
              amount: success.wallet.balance,
              symbol: TOKEN_SHORT_CODE,
            })}
          </span>
        </div>
      </div>

      {success.first_purchase_reward ? (
        <RewardCard
          title={success.first_purchase_reward.title}
          description={success.first_purchase_reward.description}
          amount={success.first_purchase_reward.amount}
        />
      ) : null}

      {success.locked_cashback_reward ? (
        <RewardCard
          title={success.locked_cashback_reward.title}
          description={success.locked_cashback_reward.description}
          amount={success.locked_cashback_reward.amount}
        />
      ) : null}

      {success.second_purchase_challenge_reward ? (
        <RewardCard
          title={success.second_purchase_challenge_reward.title}
          description={success.second_purchase_challenge_reward.description}
          amount={success.second_purchase_challenge_reward.amount}
        />
      ) : null}

      {successRewardCopy?.title || successRewardCopy?.body || successDiscountCode ? (
        <div className="pv-card-muted p-4">
          {successRewardCopy?.title ? (
            <p className="text-sm font-semibold text-zinc-900">{successRewardCopy.title}</p>
          ) : null}
          {successRewardCopy?.body ? (
            <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-600">{successRewardCopy.body}</p>
          ) : null}
          {successDiscountCode ? (
            <div className="mt-3 inline-flex rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-900">
              {successDiscountCode}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function RewardCard({
  title,
  description,
  amount,
}: {
  title: string;
  description: string | null;
  amount: number | null;
}) {
  return (
    <div className="pv-card-muted p-4">
      <p className="text-sm font-semibold text-zinc-900">{title}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        {amount ? <LmnAmount amount={`+${amount}`} symbol={TOKEN_SHORT_CODE} state="earned" /> : null}
        {description ? <p className="text-sm text-zinc-600">{description}</p> : null}
      </div>
    </div>
  );
}
