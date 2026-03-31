"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { ApiRequestError } from "@/lib/api";
import {
  STORE_KIND_TONE,
  STORE_NEAR_MISS_ITEMS_LIMIT,
  STORE_SECTION_ORDER,
  STORE_SUCCESS_CLEAR_TIMEOUT_MS,
} from "@/lib/constants/economy-ui";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getAffordableStoreItems, getNearMissStoreItems, pickBestStoreItem, sortStoreItems } from "@/lib/economy";
import { fetchStoreItems, fetchWallet, purchaseStoreItem } from "@/lib/client-api";
import { formatNumber, humanizeSnakeCase } from "@/lib/formatters";
import { languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import type { PurchaseResult, StoreItem, StoreItemKind, WalletRead } from "@/lib/types";

type TranslateFn = ReturnType<typeof useI18n>["t"];
type TranslationParams = Record<string, string | number | null | undefined>;

function kindLabel(kind: StoreItem["kind"], t: TranslateFn) {
  const key = `store.kind.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kind : translated;
}

function sectionLabel(kind: StoreItem["kind"], t: TranslateFn) {
  const key = `store.section.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kindLabel(kind, t) : translated;
}

function tagLabel(tag: string, t: TranslateFn) {
  const key = `store.tag.${tag}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(tag) : translated;
}

function priceBandLabel(priceBand: StoreItem["price_band"], t: TranslateFn) {
  const key = `store.priceBand.${priceBand}` as TranslationKey;
  const translated = t(key);
  return translated === key ? priceBand : translated;
}

function translationOrNull(t: TranslateFn, key: TranslationKey, params?: TranslationParams): string | null {
  const translated = t(key, params);
  return translated === key ? null : translated;
}

function textOrNull(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function extractPromptTitle(item: StoreItem): string {
  const fromMeta = textOrNull(item.metadata?.prompt_title);
  if (fromMeta) return fromMeta;

  const normalized = item.title.trim();
  if (normalized.toLowerCase().startsWith("unlock:")) {
    return normalized.slice("unlock:".length).trim();
  }
  return normalized;
}

function localizedStoreItemTitle(item: StoreItem, t: TranslateFn): string {
  const key = `store.item.${item.slug}.title` as TranslationKey;
  const directTranslation = translationOrNull(t, key);
  if (directTranslation) return directTranslation;

  if (item.kind === "premium_prompt_unlock" || item.slug.startsWith("unlock-")) {
    const dynamicTranslation = translationOrNull(t, "store.item.dynamicUnlock.title", {
      title: extractPromptTitle(item),
    });
    if (dynamicTranslation) return dynamicTranslation;
  }
  return item.title;
}

function localizedStoreItemDescription(item: StoreItem, t: TranslateFn): string | null {
  const key = `store.item.${item.slug}.description` as TranslationKey;
  const directTranslation = translationOrNull(t, key);
  if (directTranslation) return directTranslation;

  if (item.kind === "premium_prompt_unlock" || item.slug.startsWith("unlock-")) {
    const dynamicTranslation = translationOrNull(t, "store.item.dynamicUnlock.description");
    if (dynamicTranslation) return dynamicTranslation;
  }
  return textOrNull(item.description);
}

function localizedStarterReward(args: {
  slug: string;
  t: TranslateFn;
  fallbackTitle: string | null;
  fallbackBody: string | null;
}) {
  const title = translationOrNull(args.t, `store.item.${args.slug}.rewardTitle` as TranslationKey) ?? args.fallbackTitle;
  const body = translationOrNull(args.t, `store.item.${args.slug}.rewardBody` as TranslationKey) ?? args.fallbackBody;
  return { title, body };
}

function formatOfferRemainingHours(iso: string | null): number | null {
  if (!iso) return null;
  const ms = new Date(iso).getTime() - Date.now();
  if (Number.isNaN(ms) || ms <= 0) return 0;
  return Math.ceil(ms / (1000 * 60 * 60));
}

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
    setLoading(true);
    Promise.allSettled([fetchStoreItems(), fetchWallet()])
      .then(([itemsResult, walletResult]) => {
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
        setError(e instanceof ApiRequestError ? e.message : t("store.purchaseFailed"));
      })
      .finally(() => setLoading(false));
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
                symbol={wallet?.currency_symbol ?? "LMN"}
                caption={wallet?.currency_name ?? wallet?.currency_symbol ?? "LMN"}
                delta={balanceDelta}
                change={balanceChange}
              />
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("store.availableNow")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{formatNumber(affordableItems.length, locale)}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("store.almostThere")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {formatNumber(bestItem?.remaining_lumens ?? 0, locale)}
              </p>
            </div>
          </div>
        }
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <EconomyLoop activeStep="store" />
      </section>

      {success ? (
        <section className="space-y-3">
          <div className="pv-alert pv-alert-success flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium">
                {t("store.purchased")}: {successPurchaseItemTitle ?? success.purchase.item.title}
              </p>
              <p className="mt-1 text-sm text-emerald-900/80">{t("store.balanceAfter")}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <LmnAmount amount={`-${success.purchase.price_paid}`} symbol={wallet?.currency_symbol ?? "LMN"} state="spent" />
              <span aria-hidden="true" className="text-sm font-semibold text-emerald-900/70">
                →
              </span>
              <LmnAmount amount={success.wallet.balance} symbol={wallet?.currency_symbol ?? "LMN"} strong state="balance" />
            </div>
          </div>

          {success.first_purchase_reward ? (
            <div className="pv-card-muted p-4">
              <p className="text-sm font-semibold text-zinc-900">{success.first_purchase_reward.title}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {success.first_purchase_reward.amount ? (
                  <LmnAmount amount={`+${success.first_purchase_reward.amount}`} symbol={wallet?.currency_symbol ?? "LMN"} state="earned" />
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
                  <LmnAmount amount={`+${success.locked_cashback_reward.amount}`} symbol={wallet?.currency_symbol ?? "LMN"} state="earned" />
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
                  <LmnAmount amount={`+${success.second_purchase_challenge_reward.amount}`} symbol={wallet?.currency_symbol ?? "LMN"} state="earned" />
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
              <p className="pv-kicker">{t("store.availableNow")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("store.availableNow")}</h2>
              <p className="mt-2 max-w-2xl text-sm text-zinc-600">{t("store.availableNowBody")}</p>
            </div>
          </div>
          <div className={`grid gap-4 ${affordableItems.length > 1 ? "md:grid-cols-2" : ""}`}>
            {affordableItems.map((item) => (
              <StoreItemCard
                key={`available-${item.id}`}
                item={item}
                wallet={wallet}
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
                wallet={wallet}
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
                  wallet={wallet}
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

function StoreItemCard({
  item,
  wallet,
  purchasing,
  onPurchase,
  locale,
}: {
  item: StoreItem;
  wallet: WalletRead | null;
  purchasing: string | null;
  onPurchase: (item: StoreItem) => Promise<void>;
  locale: string;
}) {
  const { t } = useI18n();
  const soldOut = item.availability !== null && item.availability <= 0;
  const disabled = purchasing === item.slug || soldOut || item.owned || !item.is_affordable;
  const promptTitles = Array.isArray(item.metadata?.prompt_titles) ? (item.metadata?.prompt_titles as string[]) : [];
  const progressPct = Math.max(item.progress_ratio > 0 ? 8 : 0, Math.min(100, Math.round(item.progress_ratio * 100)));
  const tone = getStoreTone(item.kind);
  const offerRemainingHours = formatOfferRemainingHours(item.offer_ends_at);
  const title = localizedStoreItemTitle(item, t);
  const description = localizedStoreItemDescription(item, t);
  const starterRewardCopy = localizedStarterReward({
    slug: item.slug,
    t,
    fallbackTitle: textOrNull(item.metadata?.reward_title),
    fallbackBody: textOrNull(item.metadata?.reward_body),
  });

  return (
    <article className="pv-card flex flex-col justify-between gap-5 p-5">
      <div className={`pointer-events-none absolute right-4 top-4 h-20 w-20 rounded-full blur-2xl ${tone.glow}`} />
      <div className="relative flex h-full flex-col gap-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <span className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${tone.badge}`}>
                {kindLabel(item.kind, t)}
              </span>
              <span className="pv-badge">{priceBandLabel(item.price_band, t)}</span>
              {item.tags.map((tag) => (
                <span key={`${item.slug}-${tag}`} className={tag === "best_value" ? "pv-badge-success" : "pv-badge-brand"}>
                  {tagLabel(tag, t)}
                </span>
              ))}
              {item.is_limited_offer ? (
                <span className="pv-badge-danger">
                  {offerRemainingHours !== null
                    ? t("store.offerEndsIn", { time: `${formatNumber(offerRemainingHours, locale)}h` })
                    : t("store.limitedOffer")}
                </span>
              ) : null}
            </div>
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">{title}</h3>
            {description ? <p className="text-sm leading-relaxed text-zinc-600">{description}</p> : null}
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("store.price")}</span>
            <LmnAmount
              amount={formatNumber(item.price, locale)}
              symbol={wallet?.currency_symbol ?? "LMN"}
              className="shrink-0"
              strong
              state="spent"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="pv-badge">
            {t("store.availability")}: {item.availability ?? "∞"}
          </span>
          {item.owned ? <span className="pv-badge-success">{t("store.owned")}</span> : null}
          {soldOut ? <span className="pv-badge-danger">{t("store.soldOut")}</span> : null}
          {!soldOut && !item.owned && item.is_affordable ? (
            <span className="pv-badge-success">{t("store.availableNow")}</span>
          ) : null}
          {!soldOut && !item.owned && !item.is_affordable ? (
            <span className="pv-badge-warning">{t("store.needMore", { count: formatNumber(item.near_miss_delta, locale) })}</span>
          ) : null}
          {item.dynamic_offer ? <span className="pv-badge-brand">{t("store.personalized")}</span> : null}
          {item.upgrade_tier > 1 ? <span className="pv-badge">{t("store.tierLabel", { tier: item.upgrade_tier })}</span> : null}
        </div>

        {!item.owned && !soldOut ? (
          <div className="pv-card-muted p-3">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-zinc-900">
                {item.is_affordable
                  ? t("store.availableNow")
                  : t("store.needMore", { count: formatNumber(item.near_miss_delta, locale) })}
              </span>
              <span className="text-zinc-500">{progressPct}%</span>
            </div>
            <div className="mt-3 pv-progress">
              <div className="pv-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        ) : null}

        {promptTitles.length > 0 ? (
          <div className="pv-card-muted p-3 text-sm text-zinc-600">{promptTitles.join(" · ")}</div>
        ) : null}

        {item.kind === "starter" && (starterRewardCopy.title || starterRewardCopy.body) ? (
          <div className="pv-card-muted p-3 text-sm text-zinc-600">
            {starterRewardCopy.title ? <span className="font-medium text-zinc-900">{starterRewardCopy.title}</span> : null}
            {starterRewardCopy.body ? <p className="mt-1">{starterRewardCopy.body}</p> : null}
          </div>
        ) : null}

        {wallet && item.is_affordable && !soldOut && !item.owned ? (
          <div className="pv-card-muted p-3">
            <p className="pv-stat-label">{t("store.balanceAfter")}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} state="balance" />
              <span aria-hidden="true" className="text-sm font-semibold text-zinc-400">
                →
              </span>
              <LmnAmount amount={wallet.balance - item.price} symbol={wallet.currency_symbol} state="balance" />
            </div>
          </div>
        ) : null}

        {item.owned ? (
          <button
            type="button"
            disabled
            className={`mt-auto inline-flex items-center justify-center rounded-full px-4 py-3 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${tone.button}`}
          >
            {t("store.owned")}
          </button>
        ) : soldOut ? (
          <button
            type="button"
            disabled
            className={`mt-auto inline-flex items-center justify-center rounded-full px-4 py-3 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${tone.button}`}
          >
            {t("store.soldOut")}
          </button>
        ) : item.is_affordable ? (
          <button
            type="button"
            onClick={() => void onPurchase(item)}
            disabled={disabled}
            className={`mt-auto inline-flex items-center justify-center rounded-full px-4 py-3 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${tone.button}`}
          >
            {purchasing === item.slug ? t("missions.loading") : t("store.purchase")}
          </button>
        ) : (
          <Link href={APP_ROUTES.missions} className="pv-button-secondary mt-auto !w-auto justify-center">
            {t("economy.earnCta")}
          </Link>
        )}
      </div>
    </article>
  );
}

function getStoreTone(kind: StoreItemKind) {
  return STORE_KIND_TONE[kind];
}
