import { API_ENDPOINTS } from "../constants/api";
import type { BillingStatus, CheckoutSessionResult } from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchBillingStatus(): Promise<BillingStatus> {
  return authFetch<BillingStatus>(API_ENDPOINTS.billingSubscription);
}

export async function createCheckoutSession(tier: string): Promise<CheckoutSessionResult> {
  return authFetch<CheckoutSessionResult>(API_ENDPOINTS.billingCheckoutSession, jsonInit("POST", { tier }));
}

export async function createBillingPortalSession(): Promise<{ url: string }> {
  return authFetch<{ url: string }>(API_ENDPOINTS.billingPortal, jsonInit("POST", {}));
}
