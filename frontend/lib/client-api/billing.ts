import { API_ENDPOINTS } from "../constants/api";
import type { BillingStatus, CheckoutSessionResult } from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchBillingStatus(): Promise<BillingStatus> {
  return authFetch<BillingStatus>(API_ENDPOINTS.billingSubscription);
}

export async function createCheckoutSession(
  tier: string,
  options?: {
    sourcePage?: string;
    scenarioSlug?: string;
    paywallVariant?: string;
    pricingVariant?: string;
  },
): Promise<CheckoutSessionResult> {
  return authFetch<CheckoutSessionResult>(
    API_ENDPOINTS.billingCheckoutSession,
    jsonInit("POST", {
      tier,
      source_page: options?.sourcePage ?? null,
      scenario_slug: options?.scenarioSlug ?? null,
      paywall_variant: options?.paywallVariant ?? null,
      pricing_variant: options?.pricingVariant ?? null,
    }),
  );
}

export async function createBillingPortalSession(): Promise<{ url: string }> {
  return authFetch<{ url: string }>(API_ENDPOINTS.billingPortal, jsonInit("POST", {}));
}
