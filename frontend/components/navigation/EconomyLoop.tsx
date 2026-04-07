"use client";

import type { ReactNode } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { RouteCard } from "@/components/navigation/RouteCard";

type EconomyLoopCardProps = {
  title?: ReactNode;
  description?: ReactNode;
  href?: string;
  actionLabel?: ReactNode;
  badge?: ReactNode;
};

type EconomyLoopProps = {
  activeStep?: "missions" | "wallet" | "store";
  missionCard?: EconomyLoopCardProps;
  walletCard?: EconomyLoopCardProps;
  storeCard?: EconomyLoopCardProps;
};

export function EconomyLoop({ activeStep, missionCard, walletCard, storeCard }: EconomyLoopProps) {
  const { t } = useI18n();

  return (
    <div className="pv-economy-loop space-y-4">
      <div className="space-y-2">
        <p className="pv-kicker">{t("economy.loopTitle")}</p>
        <p className="text-sm leading-relaxed text-zinc-600">{t("economy.loopBody")}</p>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <RouteCard
          eyebrow={t("nav.missions")}
          title={missionCard?.title ?? t("economy.stepEarnTitle")}
          description={missionCard?.description ?? t("missions.subtitle")}
          href={missionCard?.href ?? "/missions"}
          actionLabel={missionCard?.actionLabel ?? t("nav.missions")}
          badge={missionCard?.badge}
          active={activeStep === "missions"}
          tone="neutral"
        />
        <RouteCard
          eyebrow={t("nav.wallet")}
          title={walletCard?.title ?? t("economy.stepBalanceTitle")}
          description={walletCard?.description ?? t("wallet.subtitle")}
          href={walletCard?.href ?? "/wallet"}
          actionLabel={walletCard?.actionLabel ?? t("nav.wallet")}
          badge={walletCard?.badge}
          active={activeStep === "wallet"}
          tone="neutral"
        />
        <RouteCard
          eyebrow={t("nav.store")}
          title={storeCard?.title ?? t("economy.stepSpendTitle")}
          description={storeCard?.description ?? t("store.subtitle")}
          href={storeCard?.href ?? "/store"}
          actionLabel={storeCard?.actionLabel ?? t("nav.store")}
          badge={storeCard?.badge}
          active={activeStep === "store"}
          tone="neutral"
        />
      </div>
    </div>
  );
}
