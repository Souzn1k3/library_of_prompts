"use client";

import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatMultiplier, formatNumber } from "@/lib/formatters";
import type { StoreItem, WalletRead } from "@/lib/types";
import type { WalletTranslate } from "@/components/wallet/walletPresentation";

type WalletBreadcrumb = Array<{ label: string; href?: string }>;

type WalletHeroProps = {
  breadcrumbs: WalletBreadcrumb;
  t: WalletTranslate;
  locale: string;
  wallet: WalletRead;
  checkinPending: boolean;
  onCheckIn: () => void;
  bestItem: StoreItem | null;
  checkInMessage: string;
  balanceChange: "up" | "down" | null;
  balanceDelta: number | null;
};

export function WalletHero({
  breadcrumbs,
  t,
  locale,
  wallet,
  checkinPending,
  onCheckIn,
  bestItem,
  checkInMessage,
  balanceChange,
  balanceDelta,
}: WalletHeroProps) {
  return (
    <PageIntro
      breadcrumbs={breadcrumbs}
      eyebrow={t("nav.wallet")}
      title={t("wallet.title")}
      description={t("wallet.subtitle")}
      hint={
        bestItem
          ? bestItem.is_affordable
            ? t("wallet.bestUseReady", { title: bestItem.title })
            : t("wallet.bestUseAlmost", { title: bestItem.title, count: bestItem.remaining_lumens })
          : checkInMessage
      }
      actions={(
        <button
          type="button"
          onClick={onCheckIn}
          disabled={checkinPending || !wallet.check_in_available}
          className="pv-button-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          {checkinPending ? t("missions.loading") : t("wallet.checkinCta")}
        </button>
      )}
      aside={(
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
          <div className="sm:col-span-3 xl:col-span-1">
            <LmnBalanceCard
              label={t("wallet.balance")}
              amount={wallet.balance}
              symbol={TOKEN_SHORT_CODE}
              caption={t("wallet.currencyHint")}
              detail={wallet.check_in_available ? t("wallet.checkinReady") : t("wallet.checkinLocked")}
              delta={balanceDelta}
              change={balanceChange}
              showIcon
              compactCode={false}
            />
          </div>
          <div className="pv-stat-card">
            <p className="pv-stat-label">{t("wallet.currentStreak")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{wallet.current_streak}</p>
          </div>
          <div className="pv-stat-card">
            <p className="pv-stat-label">{t("wallet.spendStreak")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
              {t("wallet.spendStreakValue", {
                days: formatNumber(wallet.spend_streak_days, locale),
                mult: formatMultiplier(wallet.spend_streak_mult, locale),
              })}
            </p>
          </div>
        </div>
      )}
    />
  );
}
