"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { StoreItemCard } from "@/components/store/StoreItemCard";
import {
  localizedStarterReward,
  localizedStoreItemTitle,
  sectionLabel,
  textOrNull,
} from "@/components/store/presentation";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { ApiRequestError } from "@/lib/api";
import {
  STORE_NEAR_MISS_ITEMS_LIMIT,
  STORE_SECTION_ORDER,
  STORE_SUCCESS_CLEAR_TIMEOUT_MS,
} from "@/lib/constants/economy-ui";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getAffordableStoreItems, getNearMissStoreItems, pickBestStoreItem, sortStoreItems } from "@/lib/economy";
import { fetchStoreItems, fetchWallet, purchaseStoreItem } from "@/lib/client-api";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import { languageToIntlLocale } from "@/lib/i18n";
import type { PurchaseResult, StoreItem, WalletRead } from "@/lib/types";

export function StoreClient() {
  const { status } = useAuth();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const [items, setItems] = useState<StoreItem[]>([]);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [success, setSuccess] = useState<PurchaseResult | null>(null);
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);

  useEffect(() => {
    if (status !== "authenticated") {
      setLoading(status === "loading");
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.allSettled([fetchStoreItems(), fetchWallet()])
      .then(([itemsResult, walletResult]) => {
        if (cancelled) return;
        let localError: string | null = null;
        if (itemsResult.status === "fulfilled") {
          setItems(sortStoreItems(itemsResult.value));
        } else {
          localError = t("store.loadFailed");
        }
        if (walletResult.status === "fulfilled") {
          setWallet(walletResult.value);
        }
        setError(localError);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof ApiRequestError ? e.message : t("store.purchaseFailed"));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, t]);

  useEffect(() => {
    if (!success) return;
    const timeoutId = window.setTimeout(() => setSuccess(null), STORE_SUCCESS_CLEAR_TIMEOUT_MS);
    return () => window.clearTimeout(timeoutId);
  }, [success]);

  const affordableItems = useMemo(() => getAffordableStoreItems(items), [items]);
  const nearMissItems = useMemo(() => getNearMissStoreItems(items, STORE_NEAR_MISS_ITEMS_LIMIT), [items]);
  const bestItem = useMemo(() => pickBestStoreItem(items), [items]);
  const bestItemTitle = bestItem ? localizedStoreItemTitle(bestItem, t) : null;
  const successPurchaseItemTitle = success ? localizedStoreItemTitle(success.purchase.item, t) : null;
  const successRewardCopy = success
    ? localizedStarterReward({
        slug: success.purchase.item.slug,
        t,
        fallbackTitle: textOrNull(success.purchase.metadata?.reward_title),
        fallbackBody: textOrNull(success.purchase.metadata?.reward_body),
      })
    : null;
  const successDiscountCode =
    success && typeof success.purchase.metadata?.discount_code === "string" ? success.purchase.metadata.discount_code : null;

  const sections = useMemo(() => {
    return STORE_SECTION_ORDER.map((kind) => ({
      kind,
      items: items.filter((item) => item.kind === kind),
    })).filter((section) => section.items.length > 0);
  }, [items]);

  async function handlePurchase(item: StoreItem) {
    const clientToken =
      typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${item.slug}-${Date.now()}`;
    setPurchasing(item.slug);
    setSuccess(null);
    try {
      const result = await purchaseStoreItem(item.slug, clientToken);
      const refreshedItems = await fetchStoreItems();
      setWallet(result.wallet);
      setItems(sortStoreItems(refreshedItems));
      setError(null);
      setSuccess(result);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : t("store.purchaseFailed"));
    } finally {
      setPurchasing(null);
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.store") },
          ]}
          eyebrow={t("nav.store")}
          title={t("store.title")}
          description={t("store.subtitle")}
          hint={t("economy.loopBody")}
        />
        <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.store") },
          ]}
          eyebrow={t("nav.store")}
          title={t("store.title")}
          description={t("store.subtitle")}
          hint={t("store.guestHint")}
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("store.signInPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
            {t("store.signInLink")}
          </Link>{" "}
          {t("store.signInSuffix")}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={[
          { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
          { label: t("nav.economy") },
          { label: t("nav.store") },
        ]}
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
            <Link href={affordableItems.length > 0 ? APP_ROUTES.wallet : APP_ROUTES.missions} className="pv-button-primary">
              {affordableItems.length > 0 ? t("nav.wallet") : t("economy.earnCta")}
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
                amount={wallet?.balance ?? "—"}
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
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{formatNumber(affordableItems.length, locale)}</p>
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

      {success ? (
        <section className="space-y-3">
          <div className="pv-alert pv-alert-success flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium">
                {t("store.purchased")}: {successPurchaseItemTitle ?? success.purchase.item.title}
              </p>
              <p className="mt-1 text-sm text-emerald-900/80">
                {t("store.purchaseSummarySpent", {
                  amount: success.purchase.price_paid,
                  symbol: TOKEN_SHORT_CODE,
                })}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <LmnAmount amount={`-${success.purchase.price_paid}`} symbol={TOKEN_SHORT_CODE} state="spent" />
              <span className="pv-chip">
                {t("store.currentBalance", {
                  amount: success.wallet.balance,
                  symbol: TOKEN_SHORT_CODE,
                })}
              </span>
            </div>
          </div>

          {success.first_purchase_reward ? (
            <div className="pv-card-muted p-4">
              <p className="text-sm font-semibold text-zinc-900">{success.first_purchase_reward.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {success.first_purchase_reward.amount ? (
                  <LmnAmount amount={`+${success.first_purchase_reward.amount}`} symbol={TOKEN_SHORT_CODE} state="earned" />
                ) : null}
                <p className="text-sm text-zinc-600">{success.first_purchase_reward.description}</p>
              </div>
            </div>
          ) : null}

          {success.locked_cashback_reward ? (
            <div className="pv-card-muted p-4">
              <p className="text-sm font-semibold text-zinc-900">{success.locked_cashback_reward.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {success.locked_cashback_reward.amount ? (
                  <LmnAmount amount={`+${success.locked_cashback_reward.amount}`} symbol={TOKEN_SHORT_CODE} state="earned" />
                ) : null}
                <p className="text-sm text-zinc-600">{success.locked_cashback_reward.description}</p>
              </div>
            </div>
          ) : null}

          {success.second_purchase_challenge_reward ? (
            <div className="pv-card-muted p-4">
              <p className="text-sm font-semibold text-zinc-900">{success.second_purchase_challenge_reward.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {success.second_purchase_challenge_reward.amount ? (
                  <LmnAmount amount={`+${success.second_purchase_challenge_reward.amount}`} symbol={TOKEN_SHORT_CODE} state="earned" />
                ) : null}
                <p className="text-sm text-zinc-600">{success.second_purchase_challenge_reward.description}</p>
              </div>
            </div>
          ) : null}

          {successRewardCopy?.title || successRewardCopy?.body || successDiscountCode ? (
            <div className="pv-card-muted p-4">
              {successRewardCopy?.title ? (
                <p className="text-sm font-semibold text-zinc-900">{successRewardCopy.title}</p>
              ) : null}
              {successRewardCopy?.body ? (
                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-600">
                  {successRewardCopy.body}
                </p>
              ) : null}
              {successDiscountCode ? (
                <div className="mt-3 inline-flex rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-900">
                  {successDiscountCode}
                </div>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {error ? <div className="pv-alert pv-alert-warning">{error}</div> : null}

      {affordableItems.length > 0 ? (
        <section className="space-y-3">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("store.readySectionKicker")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("store.availableNow")}</h2>
              <p className="mt-2 max-w-2xl text-sm text-zinc-600">{t("store.availableNowBody")}</p>
            </div>
          </div>
          <div className={`grid gap-4 ${affordableItems.length > 1 ? "md:grid-cols-2" : ""}`}>
            {affordableItems.map((item) => (
              <StoreItemCard
                key={`available-${item.id}`}
                item={item}
                purchasing={purchasing}
                onPurchase={handlePurchase}
                locale={locale}
              />
            ))}
          </div>
        </section>
      ) : null}

      {nearMissItems.length > 0 ? (
        <section className="space-y-3">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("store.almostThere")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("store.almostThere")}</h2>
              <p className="mt-2 max-w-2xl text-sm text-zinc-600">{t("store.almostThereBody")}</p>
            </div>
          </div>
          <div className={`grid gap-4 ${nearMissItems.length > 1 ? "md:grid-cols-2 xl:grid-cols-3" : ""}`}>
            {nearMissItems.map((item) => (
              <StoreItemCard
                key={`near-miss-${item.id}`}
                item={item}
                purchasing={purchasing}
                onPurchase={handlePurchase}
                locale={locale}
              />
            ))}
          </div>
        </section>
      ) : null}

      {sections.length === 0 ? (
        <div className="pv-empty-state text-sm text-zinc-600">{t("store.empty")}</div>
      ) : (
        sections.map((section) => (
          <section key={section.kind} className="space-y-3">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  {sectionLabel(section.kind, t)}
                </h2>
              </div>
            </div>

            <div className={`grid gap-4 ${section.items.length > 1 ? "md:grid-cols-2" : ""}`}>
              {section.items.map((item) => (
                <StoreItemCard
                  key={item.id}
                  item={item}
                  purchasing={purchasing}
                  onPurchase={handlePurchase}
                  locale={locale}
                />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
