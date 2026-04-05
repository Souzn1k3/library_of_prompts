"use client";

import { formatNumber } from "@/lib/formatters";
import type { WalletRead } from "@/lib/types";
import {
  localizedGoalCopy,
  type WalletTranslate,
} from "@/components/wallet/walletPresentation";

type WalletGoalsSectionProps = {
  goals: WalletRead["goals"];
  locale: string;
  t: WalletTranslate;
};

export function WalletGoalsSection({ goals, locale, t }: WalletGoalsSectionProps) {
  if (goals.length === 0) {
    return null;
  }

  return (
    <section className="pv-panel px-5 py-5">
      <p className="pv-kicker">{t("wallet.activeGoals")}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {goals.map((goal) => {
          const localizedGoal = localizedGoalCopy(goal, t);
          return (
            <div key={goal.key} className="pv-card-muted p-4">
              <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">
                {localizedGoal.layer}
              </p>
              <p className="mt-2 text-sm font-semibold text-zinc-900">{localizedGoal.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{localizedGoal.description}</p>
              <p className="mt-2 text-xs text-zinc-500">
                {formatNumber(goal.progress, locale)}/{formatNumber(goal.target, locale)}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
