"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PurchaseReviewCard } from "@/components/profile/PurchaseReviewCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import type {
  PromptMarketplacePurchase,
  SellerMarketplaceSummary,
} from "@/lib/types";

type ProfilePurchasesSectionProps = {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  locale: string;
  onReload: () => void;
};

export function ProfilePurchasesSection({
  summary,
  purchases,
  locale,
  onReload,
}: ProfilePurchasesSectionProps) {
  const { t } = useI18n();

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="pv-kicker">{t("profile.purchasesLibraryKicker")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("profile.recentPurchasesTitle")}
          </h2>
          <p className="mt-2 text-sm text-zinc-600">{t("profile.recentPurchasesDescription")}</p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-zinc-500">
            <span className="pv-chip">{t("profile.recentPurchasesFlowOpen")}</span>
            <span className="pv-chip">{t("profile.recentPurchasesFlowRate")}</span>
            <span className="pv-chip">{t("profile.recentPurchasesFlowSave")}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="pv-chip">
            {t("profile.totalPurchasesCount", { count: summary.purchases_count })}
          </span>
          <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
            {t("footer.browsePrompts")}
          </Link>
        </div>
      </div>

      {purchases.length ? (
        <div className="mt-6 space-y-4">
          {purchases.map((purchase) => (
            <PurchaseReviewCard
              key={purchase.id}
              locale={locale}
              purchase={purchase}
              onSubmitted={onReload}
            />
          ))}
        </div>
      ) : (
        <p className="mt-6 text-sm text-zinc-500">{t("profile.noPurchases")}</p>
      )}
    </section>
  );
}
