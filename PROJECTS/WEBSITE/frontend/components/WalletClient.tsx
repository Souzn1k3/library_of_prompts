"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { fetchWallet, walletCheckIn } from "@/lib/client-api";
import type { CurrencyTransaction, WalletBenefit, WalletPurchase, WalletRead } from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n";

function formatAmount(amount: number): string {
  const sign = amount > 0 ? "+" : "";
  return `${sign}${amount}`;
}

function reasonLabel(reason: string, t: ReturnType<typeof useI18n>["t"]): string {
  const key = `wallet.transaction.reason.${reason}` as TranslationKey;
  const translated = t(key);
  return translated === key ? reason : translated;
}

function benefitLabel(benefit: WalletBenefit, t: ReturnType<typeof useI18n>["t"]) {
  if (benefit.kind === "subscription_discount") {
    const code = typeof benefit.metadata?.code === "string" ? benefit.metadata.code : null;
    const percent = benefit.metadata?.discount_percent;
    return code ? `${percent ?? ""}% · ${code}` : t("store.kind.subscription_discount");
  }
  if (benefit.kind === "premium_access") {
    return t("store.kind.premium_pass");
  }
  if (benefit.kind === "premium_prompt_unlock") {
    return typeof benefit.metadata?.prompt_title === "string"
      ? String(benefit.metadata.prompt_title)
      : t("store.kind.premium_prompt_unlock");
  }
  if (benefit.kind === "prompt_bundle") {
    return typeof benefit.metadata?.item_title === "string"
      ? String(benefit.metadata.item_title)
      : t("store.kind.prompt_bundle");
  }
  return benefit.kind;
}

export function WalletClient() {
  const { status } = useAuth();
  const { t } = useI18n();
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkinPending, setCheckinPending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (status !== "authenticated") return;
    setLoading(true);
    fetchWallet()
      .then((data) => {
        setWallet(data);
        setError(null);
      })
      .catch((e) => {
        setWallet(null);
        setError(e instanceof ApiRequestError ? e.message : t("wallet.checkInError"));
      })
      .finally(() => setLoading(false));
  }, [status, reloadToken, t]);

  async function handleCheckIn() {
    setCheckinPending(true);
    try {
      const data = await walletCheckIn();
      setWallet(data);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : t("wallet.checkInError"));
    } finally {
      setCheckinPending(false);
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

  if (error) {
    return (
      <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setReloadToken((v) => v + 1)}
            className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
          >
            {t("wallet.refresh")}
          </button>
          <button
            type="button"
            onClick={handleCheckIn}
            className="rounded-md bg-amber-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-amber-800"
          >
            {t("wallet.checkinCta")}
          </button>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  return (
    <div className="space-y-6">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="pv-kicker">{t("wallet.title")}</p>
            <p className="mt-2 text-4xl font-semibold tracking-[-0.05em] text-zinc-950">
              {wallet.balance} <span className="text-base font-medium text-zinc-500">{wallet.currency_symbol}</span>
            </p>
            <p className="mt-2 max-w-2xl text-sm text-zinc-600">{t("wallet.subtitle")}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={checkinPending || !wallet.check_in_available}
              className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {checkinPending ? t("missions.loading") : t("wallet.checkinCta")}
            </button>
            <Link href="/store" className="pv-button-secondary">
              {t("nav.store")}
            </Link>
            <Link href="/missions" className="pv-button-secondary">
              {t("nav.missions")}
            </Link>
          </div>
        </div>

        <p className="mt-4 text-sm text-zinc-600">
          {wallet.check_in_available
            ? t("wallet.checkinReady")
            : `${t("wallet.checkinLocked")}${wallet.last_check_in_at ? ` · ${new Date(wallet.last_check_in_at).toLocaleString()}` : ""}`}
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label={t("wallet.earned")} value={`${wallet.total_earned} ${wallet.currency_symbol}`} />
        <StatCard label={t("wallet.spent")} value={`${wallet.total_spent} ${wallet.currency_symbol}`} />
        <StatCard label={t("wallet.currentStreak")} value={String(wallet.current_streak)} tone="positive" />
        <StatCard label={t("wallet.bestStreak")} value={String(wallet.best_streak)} tone="neutral" />
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="pv-panel px-5 py-5">
          <div className="flex items-center justify-between gap-3">
            <p className="pv-kicker">{t("wallet.activeBenefits")}</p>
            <p className="text-xs text-zinc-500">{t("wallet.balance")}: {wallet.balance} {wallet.currency_symbol}</p>
          </div>
          {wallet.active_benefits.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-600">{t("wallet.noBenefits")}</p>
          ) : (
            <div className="mt-4 space-y-3">
              {wallet.active_benefits.map((benefit) => (
                <div key={benefit.key} className="rounded-[1.25rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
                  <p className="text-sm font-semibold text-zinc-900">{benefitLabel(benefit, t)}</p>
                  {benefit.expires_at ? (
                    <p className="mt-1 text-xs text-zinc-500">
                      {t("wallet.premiumUntil")}: {new Date(benefit.expires_at).toLocaleString()}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="pv-panel px-5 py-5">
          <div className="flex items-center justify-between gap-3">
            <p className="pv-kicker">{t("wallet.purchaseHistory")}</p>
            <Link href="/store" className="pv-inline-link">
              {t("nav.store")}
            </Link>
          </div>
          {wallet.recent_purchases.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-600">{t("wallet.noPurchases")}</p>
          ) : (
            <div className="mt-4 space-y-3">
              {wallet.recent_purchases.map((purchase: WalletPurchase) => (
                <div key={purchase.id} className="rounded-[1.25rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{purchase.item_title}</p>
                      <p className="mt-1 text-xs text-zinc-500">{new Date(purchase.created_at).toLocaleString()}</p>
                    </div>
                    <p className="text-sm font-medium text-zinc-700">-{purchase.price_paid} {wallet.currency_symbol}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="space-y-2 rounded-lg border border-zinc-200 bg-white p-4 shadow-card">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{t("wallet.recentActivity")}</p>
          <p className="text-xs text-zinc-500">
            {t("wallet.balance")}: {wallet.balance} {wallet.currency_symbol}
          </p>
        </div>
        {wallet.recent.length === 0 ? (
          <p className="text-sm text-zinc-600">{t("wallet.empty")}</p>
        ) : (
          <div className="divide-y divide-zinc-100">
            {wallet.recent.map((tx: CurrencyTransaction) => (
              <div key={tx.id} className="flex items-center justify-between py-2 text-sm text-zinc-800">
                <div>
                  <p className="font-medium text-zinc-900">{reasonLabel(tx.reason, t)}</p>
                  <p className="text-xs text-zinc-500">
                    {new Date(tx.created_at).toLocaleString()}
                    {tx.context ? ` · ${tx.context}` : ""}
                  </p>
                </div>
                <div className={`text-right ${tx.amount > 0 ? "text-emerald-700" : "text-zinc-700"}`}>
                  <p className="font-semibold">
                    {formatAmount(tx.amount)} {wallet.currency_symbol}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {t("wallet.balance")}: {tx.balance_after}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, tone = "neutral" }: { label: string; value: string; tone?: "neutral" | "positive" }) {
  const styles =
    tone === "positive" ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-zinc-200 bg-zinc-50 text-zinc-900";
  return (
    <div className={`rounded-lg border ${styles} p-4`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">{label}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  );
}
