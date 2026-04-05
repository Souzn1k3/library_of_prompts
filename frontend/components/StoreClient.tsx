"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { StoreItemGridSection } from "@/components/store/StoreItemGridSection";
import { StoreLoadingView, StoreUnauthenticatedView } from "@/components/store/StoreStatusViews";
import { StorePageIntro } from "@/components/store/StorePageIntro";
import { StoreSuccessSection } from "@/components/store/StoreSuccessSection";
import {
  sectionLabel,
  type TranslateFn,
} from "@/components/store/presentation";
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
    nearMissItems,
    bestItem,
    bestItemTitle,
    successPurchaseItemTitle,
    successRewardCopy,
    successDiscountCode,
    sections,
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

      {affordableItems.length > 0 ? (
        <StoreItemGridSection
          kicker={t("store.readySectionKicker")}
          title={t("store.availableNow")}
          body={t("store.availableNowBody")}
          items={affordableItems}
          purchasing={purchasing}
          onPurchase={handlePurchase}
          locale={locale}
          keyPrefix="available"
        />
      ) : null}

      {nearMissItems.length > 0 ? (
        <StoreItemGridSection
          kicker={t("store.almostThere")}
          title={t("store.almostThere")}
          body={t("store.almostThereBody")}
          items={nearMissItems}
          purchasing={purchasing}
          onPurchase={handlePurchase}
          locale={locale}
          gridClassName={nearMissItems.length > 1 ? "md:grid-cols-2 xl:grid-cols-3" : ""}
          keyPrefix="near-miss"
        />
      ) : null}

      {sections.length === 0 ? (
        <div className="pv-empty-state text-sm text-zinc-600">{t("store.empty")}</div>
      ) : (
        sections.map((section) => (
          <StoreItemGridSection
            key={section.kind}
            title={sectionLabel(section.kind, t)}
            items={section.items}
            purchasing={purchasing}
            onPurchase={handlePurchase}
            locale={locale}
            keyPrefix={section.kind}
          />
        ))
      )}
    </div>
  );
}
