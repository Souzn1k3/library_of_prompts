import { API_ENDPOINTS } from "../constants/api";
import type { BillingStatus, PlanRecord } from "../types";
import type { Language } from "../i18n";
import { apiFetch } from "./transport";

export async function fetchPlans(language?: Language | string | null): Promise<PlanRecord[]> {
  return apiFetch<PlanRecord[]>(API_ENDPOINTS.billingPlans, { language });
}

export async function fetchBillingStatus(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<BillingStatus> {
  return apiFetch<BillingStatus>(API_ENDPOINTS.billingSubscription, {
    accessToken,
    language,
    cache: "no-store",
  });
}
