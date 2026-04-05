"use client";

import Link from "next/link";

import { LmnAmount } from "@/components/ui/LmnAmount";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDateTime } from "@/lib/formatters";
import type { WalletPurchase } from "@/lib/types";
import type { WalletTranslate } from "@/components/wallet/walletPresentation";

type WalletPurchasesSectionProps = {
  purchases: WalletPurchase[];
  locale: string;
  t: WalletTranslate;
};

export function WalletPurchasesSection({
  purchases,
  locale,
  t,
}: WalletPurchasesSectionProps) {
  return (
    <section className="pv-panel px-5 py-5">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("wallet.latestPurchases")}
          </h2>
        </div>
        <Link href={APP_ROUTES.store} className="pv-inline-link">
          {t("nav.store")}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      {purchases.length === 0 ? (
        <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noPurchases")}</div>
      ) : (
        <div className="mt-5 space-y-3">
          {purchases.map((purchase) => (
            <div key={purchase.id} className="pv-card-muted p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-zinc-900">{purchase.item_title}</p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {formatDateTime(purchase.created_at, locale)}
                  </p>
                </div>
                <LmnAmount amount={`-${purchase.price_paid}`} symbol={TOKEN_SHORT_CODE} state="spent" />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
