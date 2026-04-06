"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useBillingPortal } from "@/components/billing/useBillingPortal";
import { ApiRequestError } from "@/lib/api";
import { analyticsSessionId, trackEvent } from "@/lib/analytics";
import { createCheckoutSession, fetchBillingStatus, fetchGrowthRuntime } from "@/lib/client-api";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";
import type { BillingStatus, PlanRecord } from "@/lib/types";

const TIER_RANK: Record<string, number> = {
  free: 0,
  starter: 1,
  pro: 2,
  enterprise: 3,
};

type TranslateFn = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type UsePlansClientModelArgs = {
  plans: PlanRecord[];
  preferredTier: string | null;
  billingState: string | null;
  billingSessionId: string | null;
  billingTier: string | null;
  t: TranslateFn;
};

function localizedBillingStatus(status: string | null | undefined, t: TranslateFn): string | null {
  if (!status) {
    return null;
  }
  const key = `plans.billingStatus.${status}` as TranslationKey;
  const translated = t(key);
  return translated === key ? t("plans.billingStatus.unknown") : translated;
}

export function usePlansClientModel({
  plans,
  preferredTier,
  billingState,
  billingSessionId,
  billingTier,
  t,
}: UsePlansClientModelArgs) {
  const { status, user, isAuthenticated } = useAuth();
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingTier, setPendingTier] = useState<string | null>(null);
  const [expandedTier, setExpandedTier] = useState<string | null>(preferredTier);
  const [paywallVariant, setPaywallVariant] = useState("control");
  const [pricingVariant, setPricingVariant] = useState("control");
  const { portalError, portalPending, openPortal, clearPortalError } = useBillingPortal();

  useEffect(() => {
    setExpandedTier(preferredTier);
  }, [preferredTier]);

  useEffect(() => {
    const sessionId = analyticsSessionId();
    fetchGrowthRuntime({
      sessionId,
      page: APP_ROUTES.pricing,
      feature: "pricing_paywall",
    })
      .then((runtime) => {
        const paywall = runtime.experiments.find((item) => item.key === "paywall_variant_v1");
        const pricing = runtime.experiments.find((item) => item.key === "pricing_variant_v1");
        if (paywall?.variant) {
          setPaywallVariant(paywall.variant);
        }
        if (pricing?.variant) {
          setPricingVariant(pricing.variant);
        }
      })
      .catch(() => null);
  }, []);

  useEffect(() => {
    trackEvent({
      eventName: "paywall_viewed",
      page: APP_ROUTES.pricing,
      feature: "pricing_page",
      onceKey: `paywall_viewed:pricing:${paywallVariant}:${pricingVariant}`,
      metadata: {
        paywall_variant: paywallVariant,
        pricing_variant: pricingVariant,
      },
    });
  }, [paywallVariant, pricingVariant]);

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
      .catch((error) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiRequestError && error.status === 401) {
          setBilling(null);
          return;
        }
      });

    return () => {
      cancelled = true;
    };
  }, [billingSessionId, billingState, billingTier, status, user]);

  const sortedPlans = useMemo(
    () => [...plans].sort((left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0)),
    [plans],
  );

  const currentTier = billing?.plan_tier ?? user?.plan_tier ?? "free";
  const currentBillingStatusLabel = localizedBillingStatus(billing?.status, t);
  const currentTierClass = currentTier === "enterprise" ? "text-emerald-700" : "text-zinc-900";
  const currentStatusClass = billing?.status === "active" ? "text-emerald-700" : "text-zinc-900";

  async function openBillingPortal() {
    setActionError(null);
    void clearPortalError();
    await openPortal();
  }

  async function upgrade(tier: string) {
    void clearPortalError();
    setActionError(null);
    setPendingTier(tier);
    trackEvent({
      eventName: "pricing_plan_selected",
      page: APP_ROUTES.pricing,
      feature: "pricing_plan_card",
      metadata: {
        current_tier: currentTier,
        target_tier: tier,
        paywall_variant: paywallVariant,
        pricing_variant: pricingVariant,
      },
    });
    trackEvent({
      eventName: "paywall_interaction",
      page: APP_ROUTES.pricing,
      feature: "pricing_checkout_start",
      metadata: {
        action: "upgrade_click",
        current_tier: currentTier,
        target_tier: tier,
        paywall_variant: paywallVariant,
        pricing_variant: pricingVariant,
      },
    });
    trackEvent({
      eventName: "upgrade_clicked",
      page: APP_ROUTES.pricing,
      feature: "plan_upgrade_cta",
      metadata: {
        current_tier: currentTier,
        target_tier: tier,
        paywall_variant: paywallVariant,
        pricing_variant: pricingVariant,
      },
    });
    try {
      const session = await createCheckoutSession(tier, {
        sourcePage: APP_ROUTES.pricing,
        paywallVariant,
        pricingVariant,
      });
      window.location.href = session.url;
    } catch (error) {
      setActionError(error instanceof Error ? error.message : t("plans.checkoutFailed"));
    } finally {
      setPendingTier(null);
    }
  }

  return {
    status,
    isAuthenticated,
    sortedPlans,
    currentTier,
    currentBillingStatusLabel,
    currentTierClass,
    currentStatusClass,
    actionError,
    pendingTier,
    expandedTier,
    portalError,
    portalPending,
    setExpandedTier,
    openBillingPortal,
    upgrade,
    isLowerOrEqualTier: (tier: string) => (TIER_RANK[tier] ?? 0) <= (TIER_RANK[currentTier] ?? 0),
  };
}
