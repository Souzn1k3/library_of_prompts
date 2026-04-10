"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { StoreItemCard } from "@/components/store/StoreItemCard";
import { StoreLoadingView, StoreUnauthenticatedView } from "@/components/store/StoreStatusViews";
import { StorePageIntro } from "@/components/store/StorePageIntro";
import { StoreSuccessSection } from "@/components/store/StoreSuccessSection";
import { type TranslateFn } from "@/components/store/presentation";
import { useStoreData } from "@/components/store/useStoreData";
import { useStoreViewModel } from "@/components/store/useStoreViewModel";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { APP_ROUTES } from "@/lib/constants/routes";
import { languageToIntlLocale } from "@/lib/i18n";
import type { StoreItem } from "@/lib/types";

export function StoreClient() {
  const { status } = useAuth();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const { items, wallet, loading, error, purchasing, success, purchase } = useStoreData({
    status,
    loadFailedMessage: t("store.loadFailed"),
    purchaseFailedMessage: t("store.purchaseFailed"),
  });
  const storeT: TranslateFn = t;
  const breadcrumbs = [
    { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
    { label: t("nav.economy") },
    { label: t("nav.store") },
  ];
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);
  const {
    affordableItems,
    bestItem,
    bestItemTitle,
    successPurchaseItemTitle,
    successRewardCopy,
    successDiscountCode,
    feedItems,
  } = useStoreViewModel({
    items,
    success,
    t: storeT,
  });

  async function handlePurchase(item: StoreItem) {
    await purchase(item);
  }

  if (status === "loading" || loading) {
    return <StoreLoadingView breadcrumbs={breadcrumbs} t={storeT} />;
  }

  if (status === "unauthenticated") {
    return <StoreUnauthenticatedView breadcrumbs={breadcrumbs} t={storeT} />;
  }

  return (
    <div className="space-y-6">
      <StorePageIntro
        breadcrumbs={breadcrumbs}
        t={storeT}
        locale={locale}
        affordableCount={affordableItems.length}
        bestItem={bestItem}
        bestItemTitle={bestItemTitle}
        balance={wallet?.balance ?? "—"}
        balanceDelta={balanceDelta}
        balanceChange={balanceChange}
      />

      {success ? (
        <StoreSuccessSection
          success={success}
          successPurchaseItemTitle={successPurchaseItemTitle}
          successRewardCopy={successRewardCopy}
          successDiscountCode={successDiscountCode}
          t={storeT}
        />
      ) : null}

      {error ? <div className="pv-alert pv-alert-warning">{error}</div> : null}

      {feedItems.length === 0 ? (
        <div className="pv-empty-state text-sm text-zinc-600">{t("store.empty")}</div>
      ) : (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {feedItems.map((item) => (
            <StoreItemCard
              key={`store-feed-${item.id}`}
              item={item}
              purchasing={purchasing}
              onPurchase={handlePurchase}
              locale={locale}
            />
          ))}
        </section>
      )}
    </div>
  );
}
