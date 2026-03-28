"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { fetchStoreItems, fetchWallet, purchaseStoreItem } from "@/lib/client-api";
import type { StoreItem, StoreItemKind, WalletRead } from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n";

const SECTION_ORDER: StoreItemKind[] = [
  "premium_pass",
  "subscription_discount",
  "premium_prompt_unlock",
  "prompt_bundle",
  "future",
];

function kindLabel(kind: StoreItem["kind"], t: ReturnType<typeof useI18n>["t"]) {
  const key = `store.kind.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kind : translated;
}

function sectionLabel(kind: StoreItem["kind"], t: ReturnType<typeof useI18n>["t"]) {
  const key = `store.section.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? kindLabel(kind, t) : translated;
}

export function StoreClient() {
  const { status } = useAuth();
  const { t } = useI18n();
  const [items, setItems] = useState<StoreItem[]>([]);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    setLoading(true);
    Promise.allSettled([fetchStoreItems(), fetchWallet()])
      .then(([itemsResult, walletResult]) => {
        let localError: string | null = null;
        if (itemsResult.status === "fulfilled") {
          setItems(itemsResult.value);
        } else {
          localError = t("store.empty");
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

  const sections = useMemo(() => {
    return SECTION_ORDER.map((kind) => ({
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
      setWallet(result.wallet);
      setItems((prev) =>
        prev.map((row) =>
          row.slug === item.slug
            ? {
                ...row,
                owned: row.kind === "premium_pass" ? row.owned : true,
                availability: row.availability !== null ? Math.max(0, row.availability - 1) : row.availability,
              }
            : row,
        ),
      );
      setError(null);
      setSuccess(result.purchase.item.title);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : t("store.purchaseFailed"));
    } finally {
      setPurchasing(null);
    }
  }

  if (status === "loading" || loading) {
    return <p className="text-sm text-zinc-500">{t("missions.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <p className="text-sm text-zinc-600">
        {t("missions.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("missions.signInLink")}
        </Link>{" "}
        {t("missions.signInSuffix")}
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="pv-kicker">{t("store.title")}</p>
            <p className="mt-2 max-w-2xl text-sm text-zinc-600">{t("store.subtitle")}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="rounded-full border border-[var(--pv-border)] bg-white px-4 py-2 text-sm font-semibold text-zinc-900">
              {wallet?.balance ?? "—"} {wallet?.currency_symbol ?? "LMN"}
            </div>
            <Link href="/wallet" className="pv-button-secondary">
              {t("nav.wallet")}
            </Link>
          </div>
        </div>
      </section>

      {success ? (
        <div className="rounded-[1.25rem] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {t("store.purchased")}: {success}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div>
      ) : null}

      {sections.length === 0 ? (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-6 text-sm text-zinc-600">
          {t("store.empty")}
        </div>
      ) : (
        sections.map((section) => (
          <section key={section.kind} className="space-y-3">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <p className="pv-kicker">{sectionLabel(section.kind, t)}</p>
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  {sectionLabel(section.kind, t)}
                </h2>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {section.items.map((item) => {
                const soldOut = item.availability !== null && item.availability <= 0;
                const insufficient = wallet ? wallet.balance < item.price : false;
                const disabled = purchasing === item.slug || soldOut || insufficient || item.owned;
                const promptTitles = Array.isArray(item.metadata?.prompt_titles)
                  ? (item.metadata?.prompt_titles as string[])
                  : [];

                return (
                  <article key={item.id} className="pv-card flex flex-col justify-between gap-4 p-5">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <h3 className="text-lg font-semibold text-zinc-900">{item.title}</h3>
                          {item.description ? <p className="text-sm text-zinc-600">{item.description}</p> : null}
                        </div>
                        <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                          {kindLabel(item.kind, t)}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-3 text-sm text-zinc-600">
                        <span>
                          {t("store.price")}: {item.price} {wallet?.currency_symbol ?? "LMN"}
                        </span>
                        <span>
                          {t("store.availability")}: {item.availability ?? "∞"}
                        </span>
                      </div>

                      {promptTitles.length > 0 ? (
                        <div className="rounded-[1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-3 text-sm text-zinc-600">
                          {promptTitles.join(" · ")}
                        </div>
                      ) : null}
                    </div>

                    <button
                      type="button"
                      onClick={() => handlePurchase(item)}
                      disabled={disabled}
                      className="inline-flex items-center justify-center rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {item.owned
                        ? t("store.owned")
                        : soldOut
                          ? t("store.soldOut")
                          : insufficient
                            ? t("store.insufficientFunds")
                            : purchasing === item.slug
                              ? t("missions.loading")
                              : t("store.purchase")}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>
        ))
      )}
    </div>
  );
}
