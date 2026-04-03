"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { trackEvent } from "@/lib/analytics";
import {
  createCheckoutSession,
  fetchBillingStatus,
} from "@/lib/client-api";
import { ApiRequestError } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants/routes";
import { formatNumber } from "@/lib/formatters";
import { getTierTranslationKey, languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import type { BillingStatus, PlanRecord } from "@/lib/types";

const TIER_RANK: Record<string, number> = {
  free: 0,
  starter: 1,
  pro: 2,
  enterprise: 3,
};

type PlansClientProps = {
  plans: PlanRecord[];
  error: string | null;
};

function localizedBillingStatus(
  status: string | null | undefined,
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string,
): string | null {
  if (!status) {
    return null;
  }
  const key = `plans.billingStatus.${status}` as TranslationKey;
  const translated = t(key);
  return translated === key ? t("plans.billingStatus.unknown") : translated;
}

export function PlansClient({ plans, error }: PlansClientProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const { status, user, isAuthenticated } = useAuth();
  const searchParams = useSearchParams();
  const preferredTier = searchParams.get("tier");
  const billingState = searchParams.get("billing");
  const billingSessionId = searchParams.get("session_id");
  const billingTier = searchParams.get("tier");
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingTier, setPendingTier] = useState<string | null>(null);
  const [expandedTier, setExpandedTier] = useState<string | null>(preferredTier);
  const currentTier = billing?.plan_tier ?? user?.plan_tier ?? "free";
  const currentBillingStatusLabel = localizedBillingStatus(billing?.status, t);
  const currentTierClass = currentTier === "enterprise" ? "text-emerald-700" : "text-zinc-900";
  const currentStatusClass = billing?.status === "active" ? "text-emerald-700" : "text-zinc-900";
  const { portalError, portalPending, openPortal, clearPortalError } = useBillingPortal();

  useEffect(() => {
    if (status !== "authenticated" || !user) {
      setBilling(null);
      return;
    }

    let cancelled = false;
    fetchBillingStatus()
      .then((billingStatus) => {
        if (cancelled) {
          return;
        }
        setBilling(billingStatus);
        if (billingState === "success" && (billingStatus.status === "active" || billingStatus.status === "trialing")) {
          trackEvent({
            eventName: "subscription_activated",
            page: APP_ROUTES.pricing,
            feature: "billing_return",
            onceKey: `subscription_activated:${billingSessionId ?? billingStatus.updated_at ?? user.id}`,
            metadata: {
              plan_tier: billingStatus.subscription_tier ?? user.plan_tier,
              subscription_status: billingStatus.status,
              provider: billingStatus.provider ?? null,
              session_id: billingSessionId ?? null,
              requested_tier: billingTier ?? null,
            },
          });
        }
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiRequestError && err.status === 401) {
          setBilling(null);
          return;
        }
        // Keep plans visible even if status loading fails unexpectedly.
      });

    return () => {
      cancelled = true;
    };
  }, [billingSessionId, billingState, billingTier, status, user]);

  const sortedPlans = useMemo(
    () => [...plans].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)),
    [plans],
  );

  async function upgrade(tier: string) {
    clearPortalError();
    setActionError(null);
    setPendingTier(tier);
    trackEvent({
      eventName: "upgrade_clicked",
      page: APP_ROUTES.pricing,
      feature: "plan_upgrade_cta",
      metadata: {
        current_tier: currentTier,
        target_tier: tier,
      },
    });
    try {
      const session = await createCheckoutSession(tier);
      window.location.href = session.url;
    } catch (e) {
      setActionError(e instanceof Error ? e.message : t("plans.checkoutFailed"));
    } finally {
      setPendingTier(null);
    }
  }

  return (
    <div className="space-y-6">
      {error ? (
        <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {status === "loading" ? (
        <p className="text-sm text-zinc-600">{t("dashboard.loading")}</p>
      ) : isAuthenticated ? (
        <div className="pv-panel px-5 py-5 text-sm text-zinc-700 sm:px-6">
          <p>
            {t("plans.currentTier")}:{" "}
            <span className={`font-medium ${currentTierClass}`}>{t(getTierTranslationKey(currentTier))}</span>
            {currentBillingStatusLabel ? (
              <>
                {" "}
                · {t("plans.subscriptionStatus")}:{" "}
                <span className={`font-medium ${currentStatusClass}`}>{currentBillingStatusLabel}</span>
              </>
            ) : null}
          </p>
          <div className="mt-3">
            <button
              type="button"
              onClick={() => {
                setActionError(null);
                void openPortal();
              }}
              disabled={portalPending}
              className="pv-button-secondary disabled:opacity-60"
            >
              {portalPending ? t("plans.openingCheckout") : t("plans.manageBilling")}
            </button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-zinc-600">
          <Link href={APP_ROUTES.signup} className="font-medium text-zinc-900 underline">
            {t("plans.createAccount")}
          </Link>{" "}
          {t("plans.createAccountSuffix")}
        </p>
      )}

      {actionError ?? portalError ? (
        <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {actionError ?? portalError}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {sortedPlans.map((plan) => {
          const isCurrent = plan.tier === currentTier;
          const isLowerOrEqual = (TIER_RANK[plan.tier] ?? 0) <= (TIER_RANK[currentTier] ?? 0);
          const expanded = expandedTier === plan.tier;
          const localizedTierName = t(getTierTranslationKey(plan.tier));
          const planDisplayName = localizedTierName || plan.name;
          const isMaxPlan = plan.tier === "enterprise";
          return (
            <div
              key={plan.tier}
              className={`pv-card p-5 ${
                preferredTier === plan.tier
                  ? "border-zinc-900 ring-1 ring-zinc-900/20"
                  : ""
              }`}
            >
              <div className="flex items-baseline justify-between gap-2">
                <h2 className={`text-lg font-semibold ${isMaxPlan ? "text-emerald-700" : "text-zinc-900"}`}>
                  {planDisplayName}
                </h2>
                <div className="text-right text-sm text-zinc-600">
                  <p className="font-semibold text-zinc-900">
                    {plan.price_rub_month > 0 ? `${formatNumber(plan.price_rub_month, locale)} RUB` : t("plans.priceFree")}
                  </p>
                  {plan.price_usd_month > 0 ? (
                    <p className="text-zinc-500">${formatNumber(plan.price_usd_month, locale)}{t("plans.perMonth")}</p>
                  ) : (
                    <p className="text-zinc-500">{t("plans.perMonth")}</p>
                  )}
                </div>
              </div>
              {plan.description ? <p className="mt-1 text-sm text-zinc-600">{plan.description}</p> : null}
              <div className="mt-4 grid gap-2 text-sm text-zinc-700">
                <div className="rounded-[0.75rem] border border-zinc-200 bg-white/70 p-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">{t("plans.includedPaidPrompts")}</p>
                  <p className="mt-2 text-2xl font-semibold text-zinc-950">{formatNumber(plan.monthly_paid_prompt_limit, locale)}</p>
                  <p className="mt-1 text-xs text-zinc-500">{t("plans.includedPaidPromptsBody")}</p>
                </div>
                {plan.highlights.map((item) => (
                  <div key={item} className="rounded-[0.625rem] border border-zinc-200 bg-zinc-50/80 px-3 py-2">
                    {item}
                  </div>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-500">
                <span className="pv-chip">{t("plans.directBuyDiscount", { value: plan.prompt_purchase_discount_percent })}</span>
                <span className="pv-chip">{t("plans.lumenDiscount", { value: plan.lumen_purchase_discount_percent })}</span>
              </div>
              <button
                type="button"
                onClick={() => setExpandedTier((current) => (current === plan.tier ? null : plan.tier))}
                className="mt-4 text-sm font-semibold text-[var(--pv-brand-strong)]"
              >
                {expanded ? t("plans.hideFeatures") : t("plans.showFeatures")}
              </button>
              {expanded ? (
                <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-zinc-700">
                  {plan.full_features.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
              <div className="mt-4">
                {status === "loading" ? (
                  <span className="inline-flex items-center rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
                    {t("dashboard.loading")}
                  </span>
                ) : !isAuthenticated ? (
                  <Link
                    href={APP_ROUTES.signup}
                    className="pv-button-secondary"
                  >
                    {t("plans.createAccountCta")}
                  </Link>
                ) : isCurrent ? (
                  <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-800">
                    {t("plans.currentPlan")}
                  </span>
                ) : isLowerOrEqual ? (
                  <span className="inline-flex items-center rounded-full bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
                    {t("plans.included")}
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => upgrade(plan.tier)}
                    disabled={pendingTier === plan.tier}
                    className="pv-button-primary disabled:opacity-60"
                  >
                    {pendingTier === plan.tier
                      ? t("plans.openingCheckout")
                      : t("plans.upgradeTo", { plan: planDisplayName })}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
