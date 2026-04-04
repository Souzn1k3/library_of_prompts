"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import type { EconomyAction } from "@/lib/types";

export function EconomyActionBanner({
  summary,
  ctaHref = "/store",
}: {
  summary: EconomyAction | null;
  ctaHref?: string;
}) {
  const { t } = useI18n();

  if (!summary) {
    return null;
  }

  const focusItem = summary.newly_affordable_items[0] ?? summary.best_item ?? null;
  const localizedNearMiss =
    focusItem && !focusItem.is_affordable && focusItem.remaining_lumens > 0
      ? t("store.needMoreForItem", { count: focusItem.remaining_lumens, title: focusItem.title })
      : null;
  if (summary.balance_delta <= 0 && !focusItem) {
    return null;
  }

  return (
    <section className="pv-alert pv-alert-success flex flex-wrap items-center justify-between gap-3">
      <div>
        {summary.balance_delta > 0 ? (
          <p className="font-medium">{t("economy.actionRewarded", { amount: summary.balance_delta })}</p>
        ) : (
          <p className="font-medium">{t("economy.actionUpdated")}</p>
        )}
        {focusItem ? (
          <p className="mt-1 text-sm text-emerald-900/80">
            {summary.newly_affordable_items.length > 0
              ? t("economy.actionNowAvailable", { title: focusItem.title })
              : t("economy.actionBestUse", { title: focusItem.title })}
          </p>
        ) : null}
        {localizedNearMiss ? <p className="mt-1 text-sm text-emerald-900/80">{localizedNearMiss}</p> : null}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {summary.balance_delta > 0 ? (
          <LmnAmount amount={`+${summary.balance_delta}`} symbol={TOKEN_SHORT_CODE} strong state="earned" />
        ) : null}
        {focusItem ? (
          <Link href={ctaHref} className="pv-button-secondary !w-auto">
            {t("economy.openStore")}
          </Link>
        ) : null}
      </div>
    </section>
  );
}
