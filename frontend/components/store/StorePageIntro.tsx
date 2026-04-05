"use client";

import Link from "next/link";

import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import type { StoreItem } from "@/lib/types";

import type { TranslateFn } from "./presentation";

type StoreBreadcrumb = Array<{ label: string; href?: string }>;

type StorePageIntroProps = {
  breadcrumbs: StoreBreadcrumb;
  t: TranslateFn;
  locale: string;
  affordableCount: number;
  bestItem: StoreItem | null;
  bestItemTitle: string | null;
  balance: number | string;
  balanceDelta: number | null;
  balanceChange: "up" | "down" | null;
};

export function StorePageIntro({
  breadcrumbs,
  t,
  locale,
  affordableCount,
  bestItem,
  bestItemTitle,
  balance,
  balanceDelta,
  balanceChange,
}: StorePageIntroProps) {
  return (
    <PageIntro
      breadcrumbs={breadcrumbs}
      eyebrow={t("nav.store")}
      title={t("store.title")}
      description={t("store.subtitle")}
      hint={
        bestItem ? (
          <span className="flex flex-wrap items-center gap-2">
            <span>{t("economy.actionBestUse", { title: bestItemTitle ?? bestItem.title })}</span>
            {bestItem.is_affordable ? (
              <span className="pv-badge-success">{t("store.availableNow")}</span>
            ) : (
              <span className="pv-badge-warning">{t("store.remaining", { count: bestItem.remaining_lumens })}</span>
            )}
          </span>
        ) : (
          t("economy.loopBody")
        )
      }
      actions={
        <>
          <Link href={affordableCount > 0 ? APP_ROUTES.wallet : APP_ROUTES.missions} className="pv-button-primary">
            {affordableCount > 0 ? t("nav.wallet") : t("economy.earnCta")}
          </Link>
          <Link href={APP_ROUTES.dashboard} className="pv-button-secondary">
            {t("nav.dashboard")}
          </Link>
        </>
      }
      aside={
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
          <div className="sm:col-span-3 xl:col-span-1">
            <LmnBalanceCard
              label={t("wallet.balance")}
              amount={balance}
              symbol={TOKEN_SHORT_CODE}
              caption={t("wallet.currencyHint")}
              delta={balanceDelta}
              change={balanceChange}
              showIcon
              compactCode={false}
            />
          </div>
          <div className="pv-stat-card">
            <p className="pv-stat-label">{t("store.readyToBuyCount")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{formatNumber(affordableCount, locale)}</p>
          </div>
          <div className="pv-stat-card">
            <p className="pv-stat-label">{t("store.toNextSpend")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
              {formatNumber(bestItem?.remaining_lumens ?? 0, locale)}
            </p>
          </div>
        </div>
      }
    />
  );
}
