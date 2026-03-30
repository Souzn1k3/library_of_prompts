"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { ApiRequestError } from "@/lib/api";
import { fetchWallet, walletCheckIn } from "@/lib/client-api";
import type { TranslationKey } from "@/lib/i18n";
import type { CurrencyTransaction, WalletBenefit, WalletPurchase, WalletRead } from "@/lib/types";

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
  const [successDelta, setSuccessDelta] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);

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

  useEffect(() => {
    if (!successDelta) return;
    const timeoutId = window.setTimeout(() => setSuccessDelta(null), 3200);
    return () => window.clearTimeout(timeoutId);
  }, [successDelta]);

  async function handleCheckIn() {
    setCheckinPending(true);
    try {
      const previousBalance = wallet?.balance ?? null;
      const data = await walletCheckIn();
      setWallet(data);
      setError(null);
      const delta = previousBalance !== null ? data.balance - previousBalance : null;
      setSuccessDelta(delta !== null && delta > 0 ? delta : null);
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : t("wallet.checkInError"));
      setSuccessDelta(null);
    } finally {
      setCheckinPending(false);
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: "/dashboard" },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
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
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
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

  if (error) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: "/dashboard" },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("economy.loopBody")}
        />
        <div className="pv-alert pv-alert-warning space-y-3">
          <p>{error}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setReloadToken((v) => v + 1)}
              className="pv-button-secondary !w-auto"
            >
              {t("wallet.refresh")}
            </button>
            <button
              type="button"
              onClick={handleCheckIn}
              className="pv-button-primary !w-auto"
            >
              {t("wallet.checkinCta")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  const checkInMessage = wallet.check_in_available
    ? t("wallet.checkinReady")
    : `${t("wallet.checkinLocked")}${wallet.last_check_in_at ? ` · ${new Date(wallet.last_check_in_at).toLocaleString()}` : ""}`;

  return (
    <div className="space-y-6">
      {successDelta ? (
        <section className="pv-alert pv-alert-success flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-medium">{t("wallet.checkedIn")}</p>
          </div>
          <LmnAmount amount={`+${successDelta}`} symbol={wallet.currency_symbol} strong state="earned" />
        </section>
      ) : null}

      <PageIntro
        breadcrumbs={[
          { label: t("nav.dashboard"), href: "/dashboard" },
          { label: t("nav.economy") },
          { label: t("nav.wallet") },
        ]}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={checkInMessage}
        actions={
          <>
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={checkinPending || !wallet.check_in_available}
              className="pv-button-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {checkinPending ? t("missions.loading") : t("wallet.checkinCta")}
            </button>
            <Link href="/store" className="pv-button-secondary">
              {t("nav.store")}
            </Link>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="sm:col-span-3 xl:col-span-1">
              <LmnBalanceCard
                label={t("wallet.balance")}
                amount={wallet.balance}
                symbol={wallet.currency_symbol}
                caption={wallet.currency_name || wallet.currency_symbol}
                detail={wallet.check_in_available ? t("wallet.checkinReady") : t("wallet.checkinLocked")}
                delta={balanceDelta}
                change={balanceChange}
              />
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.currentStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{wallet.current_streak}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.bestStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{wallet.best_streak}</p>
            </div>
          </div>
        }
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <EconomyLoop activeStep="wallet" />
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={t("wallet.earned")}
          value={<LmnAmount amount={wallet.total_earned} symbol={wallet.currency_symbol} state="earned" />}
          tone="positive"
        />
        <StatCard
          label={t("wallet.spent")}
          value={<LmnAmount amount={wallet.total_spent} symbol={wallet.currency_symbol} state="spent" />}
        />
        <StatCard
          label={t("wallet.activeBenefits")}
          value={<span className="pv-metric-value">{wallet.active_benefits.length}</span>}
          tone="positive"
        />
        <StatCard
          label={t("wallet.purchaseHistory")}
          value={<span className="pv-metric-value">{wallet.recent_purchases.length}</span>}
        />
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.activeBenefits")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.activeBenefits")}</h2>
            </div>
            <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} strong state="balance" />
          </div>
          {wallet.active_benefits.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noBenefits")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.active_benefits.map((benefit) => (
                <div key={benefit.key} className="pv-card-muted p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{benefitLabel(benefit, t)}</p>
                      {benefit.expires_at ? (
                        <p className="mt-1 text-xs text-zinc-500">
                          {t("wallet.premiumUntil")}: {new Date(benefit.expires_at).toLocaleString()}
                        </p>
                      ) : null}
                    </div>
                    <span className="pv-badge-brand">{benefit.kind}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.purchaseHistory")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.purchaseHistory")}</h2>
            </div>
            <Link href="/store" className="pv-inline-link">
              {t("nav.store")}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
          {wallet.recent_purchases.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noPurchases")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.recent_purchases.map((purchase: WalletPurchase) => (
                <div key={purchase.id} className="pv-card-muted p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{purchase.item_title}</p>
                      <p className="mt-1 text-xs text-zinc-500">{new Date(purchase.created_at).toLocaleString()}</p>
                    </div>
                    <LmnAmount amount={`-${purchase.price_paid}`} symbol={wallet.currency_symbol} state="spent" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="pv-panel px-5 py-5">
        <div className="pv-section-head">
          <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.recentActivity")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.recentActivity")}</h2>
            </div>
            <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} state="balance" />
          </div>

        {wallet.recent.length === 0 ? (
          <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.empty")}</div>
        ) : (
          <div className="mt-5 space-y-3">
            {wallet.recent.map((tx: CurrencyTransaction) => (
              <div key={tx.id} className="pv-card-muted p-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-1 h-2.5 w-2.5 rounded-full ${
                        tx.amount > 0 ? "bg-[var(--pv-success)]" : "bg-slate-400"
                      }`}
                    />
                    <div>
                      <p className="font-semibold text-zinc-900">{reasonLabel(tx.reason, t)}</p>
                      <p className="text-xs text-zinc-500">
                        {new Date(tx.created_at).toLocaleString()}
                        {tx.context ? ` · ${tx.context}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <LmnAmount
                      amount={formatAmount(tx.amount)}
                      symbol={wallet.currency_symbol}
                      state={tx.amount > 0 ? "earned" : "spent"}
                    />
                    <p className="mt-2 text-xs text-zinc-500">
                      {t("wallet.balance")}: {tx.balance_after}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  tone?: "neutral" | "positive";
}) {
  return (
    <div className={`pv-stat-card ${tone === "positive" ? "border-emerald-200/70 bg-emerald-50/60" : ""}`}>
      <p className="pv-stat-label">{label}</p>
      <div className="mt-3">{value}</div>
    </div>
  );
}
