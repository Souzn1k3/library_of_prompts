"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { ApiRequestError } from "@/lib/api";
import { fetchStoreItems, fetchWallet, purchaseStoreItem } from "@/lib/client-api";
import type { TranslationKey } from "@/lib/i18n";
import type { StoreItem, StoreItemKind, WalletRead } from "@/lib/types";

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
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: "/dashboard" },
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
            { label: t("nav.dashboard"), href: "/dashboard" },
            { label: t("nav.economy") },
            { label: t("nav.store") },
          ]}
          eyebrow={t("nav.store")}
          title={t("store.title")}
          description={t("store.subtitle")}
          hint={t("economy.loopBody")}
          actions={
            <>
              <Link href="/login" className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href="/signup" className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("missions.signInPrefix")}{" "}
          <Link href="/login" className="font-medium text-zinc-900 underline">
            {t("missions.signInLink")}
          </Link>{" "}
          {t("missions.signInSuffix")}
        </div>
      </div>
    );
  }

  const affordableCount = items.filter((item) => {
    if (!wallet) return false;
    const soldOut = item.availability !== null && item.availability <= 0;
    return !soldOut && !item.owned && wallet.balance >= item.price;
  }).length;

  return (
    <div className="space-y-6">
      <PageIntro
        breadcrumbs={[
          { label: t("nav.dashboard"), href: "/dashboard" },
          { label: t("nav.economy") },
          { label: t("nav.store") },
        ]}
        eyebrow={t("nav.store")}
        title={t("store.title")}
        description={t("store.subtitle")}
        hint={affordableCount > 0 ? `${t("wallet.balance")}: ${wallet?.balance ?? "—"}` : t("economy.loopBody")}
        actions={
          <>
            <Link href={affordableCount > 0 ? "/wallet" : "/missions"} className="pv-button-primary">
              {affordableCount > 0 ? t("nav.wallet") : t("nav.missions")}
            </Link>
            <Link href="/dashboard" className="pv-button-secondary">
              {t("nav.dashboard")}
            </Link>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.balance")}</p>
              <div className="mt-3">
                <LmnAmount amount={wallet?.balance ?? "—"} symbol={wallet?.currency_symbol ?? "LMN"} strong />
              </div>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("store.purchased")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {items.filter((item) => item.owned).length}
              </p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("store.purchase")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{affordableCount}</p>
            </div>
          </div>
        }
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <EconomyLoop activeStep="store" />
      </section>

      {success ? (
        <div className="pv-alert pv-alert-success">
          {t("store.purchased")}: {success}
        </div>
      ) : null}

      {error ? <div className="pv-alert pv-alert-warning">{error}</div> : null}

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
              {section.items.map((item) => {
                const soldOut = item.availability !== null && item.availability <= 0;
                const insufficient = wallet ? wallet.balance < item.price : false;
                const disabled = purchasing === item.slug || soldOut || insufficient || item.owned;
                const promptTitles = Array.isArray(item.metadata?.prompt_titles)
                  ? (item.metadata?.prompt_titles as string[])
                  : [];
                const tone = getStoreTone(item.kind);

                return (
                  <article key={item.id} className="pv-card flex flex-col justify-between gap-5 p-5">
                    <div className={`pointer-events-none absolute right-4 top-4 h-20 w-20 rounded-full blur-2xl ${tone.glow}`} />
                    <div className="relative flex h-full flex-col gap-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-2">
                          <span className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${tone.badge}`}>
                            {kindLabel(item.kind, t)}
                          </span>
                          <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">{item.title}</h3>
                          {item.description ? <p className="text-sm leading-relaxed text-zinc-600">{item.description}</p> : null}
                        </div>
                        <LmnAmount amount={item.price} symbol={wallet?.currency_symbol ?? "LMN"} strong />
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <span className="pv-badge">
                          {t("store.availability")}: {item.availability ?? "∞"}
                        </span>
                        {item.owned ? <span className="pv-badge-success">{t("store.owned")}</span> : null}
                        {soldOut ? <span className="pv-badge-danger">{t("store.soldOut")}</span> : null}
                        {!soldOut && insufficient ? (
                          <span className="pv-badge-warning">{t("store.insufficientFunds")}</span>
                        ) : null}
                      </div>

                      {promptTitles.length > 0 ? (
                        <div className="pv-card-muted p-3 text-sm text-zinc-600">{promptTitles.join(" · ")}</div>
                      ) : null}

                      <button
                        type="button"
                        onClick={() => handlePurchase(item)}
                        disabled={disabled}
                        className={`mt-auto inline-flex items-center justify-center rounded-full px-4 py-3 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${tone.button}`}
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
                    </div>
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

function getStoreTone(kind: StoreItemKind) {
  if (kind === "premium_pass") {
    return {
      badge: "border border-[rgba(37,92,255,0.18)] bg-[rgba(37,92,255,0.1)] text-[var(--pv-brand-strong)]",
      glow: "bg-[rgba(37,92,255,0.16)]",
      button: "bg-[linear-gradient(135deg,var(--pv-brand),#4d7dff)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,var(--pv-brand-strong),#3968f4)]",
    };
  }
  if (kind === "subscription_discount") {
    return {
      badge: "border border-[rgba(17,184,164,0.18)] bg-[rgba(17,184,164,0.12)] text-[var(--pv-accent-strong)]",
      glow: "bg-[rgba(17,184,164,0.16)]",
      button: "bg-[linear-gradient(135deg,var(--pv-accent),#35cbb8)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,var(--pv-accent-strong),#1fb9a5)]",
    };
  }
  if (kind === "future") {
    return {
      badge: "border border-zinc-200 bg-zinc-100 text-zinc-700",
      glow: "bg-[rgba(148,163,184,0.16)]",
      button: "bg-slate-600 hover:bg-slate-700",
    };
  }
  return {
    badge: "border border-[rgba(99,102,241,0.16)] bg-[rgba(99,102,241,0.1)] text-indigo-700",
    glow: "bg-[rgba(99,102,241,0.16)]",
    button: "bg-[linear-gradient(135deg,#4f46e5,#7268ff)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,#4338ca,#635bff)]",
  };
}
