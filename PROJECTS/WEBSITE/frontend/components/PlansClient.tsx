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
import { getTierTranslationKey } from "@/lib/i18n";
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

export function PlansClient({ plans, error }: PlansClientProps) {
  const { t } = useI18n();
  const { status, user, isAuthenticated } = useAuth();
  const searchParams = useSearchParams();
  const preferredTier = searchParams.get("tier");
  const billingState = searchParams.get("billing");
  const billingSessionId = searchParams.get("session_id");
  const billingTier = searchParams.get("tier");
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingTier, setPendingTier] = useState<string | null>(null);
  const currentTier = billing?.plan_tier ?? user?.plan_tier ?? "free";
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
            page: "/pricing",
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
      page: "/pricing",
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
            <span className="font-medium text-zinc-900">{t(getTierTranslationKey(currentTier))}</span>
            {billing?.status ? (
              <>
                {" "}
                · {t("plans.subscriptionStatus")}:{" "}
                <span className="font-medium text-zinc-900">{billing.status}</span>
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
          <Link href="/signup" className="font-medium text-zinc-900 underline">
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
                <h2 className="text-lg font-semibold text-zinc-900">{plan.name}</h2>
                <p className="text-sm text-zinc-600">
                  ${String(plan.price_usd_month)}
                  <span className="text-zinc-400">{t("plans.perMonth")}</span>
                </p>
              </div>
              {plan.description ? <p className="mt-1 text-sm text-zinc-600">{plan.description}</p> : null}
              <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-zinc-700">
                {plan.features.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              <div className="mt-4">
                {status === "loading" ? (
                  <span className="inline-flex items-center rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
                    {t("dashboard.loading")}
                  </span>
                ) : !isAuthenticated ? (
                  <Link
                    href="/signup"
                    className="pv-button-secondary"
                  >
                    {t("plans.createAccountCta")}
                  </Link>
                ) : isCurrent ? (
                  <span className="inline-flex items-center rounded-full bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
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
                      : t("plans.upgradeTo", { plan: plan.name })}
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
