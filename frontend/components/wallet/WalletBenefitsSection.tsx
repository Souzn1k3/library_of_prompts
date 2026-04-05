"use client";

import { LmnAmount } from "@/components/ui/LmnAmount";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDateTime, formatNumber } from "@/lib/formatters";
import type { WalletBenefit, WalletLockedReward } from "@/lib/types";
import {
  benefitKindLabel,
  benefitLabel,
  benefitMetaLines,
  type WalletTranslate,
} from "@/components/wallet/walletPresentation";

type WalletBenefitsSectionProps = {
  balance: number;
  activeBenefits: WalletBenefit[];
  pendingLockedRewards: WalletLockedReward[];
  locale: string;
  t: WalletTranslate;
};

export function WalletBenefitsSection({
  balance,
  activeBenefits,
  pendingLockedRewards,
  locale,
  t,
}: WalletBenefitsSectionProps) {
  return (
    <section className="pv-panel px-5 py-5">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("wallet.benefitsAndBoosts")}
          </h2>
        </div>
        <LmnAmount amount={balance} symbol={TOKEN_SHORT_CODE} strong state="balance" />
      </div>

      {activeBenefits.length === 0 ? (
        <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noBenefits")}</div>
      ) : (
        <div className="mt-5 space-y-3">
          {activeBenefits.map((benefit) => {
            const metaLines = benefitMetaLines(benefit, t, locale);
            return (
              <div key={benefit.key} className="pv-card-muted p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">
                      {benefitLabel(benefit, t, locale)}
                    </p>
                    {metaLines.map((line, index) => (
                      <p key={`${benefit.key}-meta-${index}`} className="mt-1 text-xs text-zinc-500">
                        {line}
                      </p>
                    ))}
                    {typeof benefit.metadata?.reward_body === "string" ? (
                      <p className="mt-2 text-xs text-zinc-600">
                        {String(benefit.metadata.reward_body)}
                      </p>
                    ) : null}
                  </div>
                  <span className="pv-badge-brand">{benefitKindLabel(benefit.kind, t)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {pendingLockedRewards.length > 0 ? (
        <div className="mt-5 space-y-3">
          {pendingLockedRewards.map((reward) => (
            <div key={reward.id} className="pv-card-muted p-4">
              <p className="text-sm font-semibold text-zinc-900">
                {t("wallet.pendingCashbackLocked", { amount: formatNumber(reward.amount, locale) })}
              </p>
              <p className="mt-1 text-xs text-zinc-600">
                {t("wallet.pendingCashbackMissions", {
                  completed: formatNumber(reward.completed_mission_count, locale),
                  required: formatNumber(reward.required_mission_count, locale),
                })}
                {reward.unlock_by
                  ? ` · ${t("wallet.pendingCashbackUnlockBy", {
                      date: formatDateTime(reward.unlock_by, locale),
                    })}`
                  : ""}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
