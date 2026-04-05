import { API_ENDPOINTS, apiPath } from "../constants/api";
import type {
  CheckoutSessionResult,
  MarketplaceOverview,
  PromptMarketplacePurchase,
  PromptReview,
} from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchMarketplaceOverview(): Promise<MarketplaceOverview> {
  return authFetch<MarketplaceOverview>(API_ENDPOINTS.marketplaceMe);
}

export async function buyPromptWithLumens(
  promptId: string,
  clientToken?: string,
): Promise<{ purchase: PromptMarketplacePurchase }> {
  return authFetch<{ purchase: PromptMarketplacePurchase }>(
    apiPath.marketplacePromptBuyWithLumens(promptId),
    jsonInit("POST", { client_token: clientToken ?? null }),
  );
}

export async function createPromptCheckoutSession(
  promptId: string,
  clientToken?: string,
  urls?: { success_url?: string; cancel_url?: string },
): Promise<CheckoutSessionResult & { purchase_id: string }> {
  return authFetch<CheckoutSessionResult & { purchase_id: string }>(
    API_ENDPOINTS.marketplacePromptCheckoutSession,
    jsonInit("POST", {
      prompt_id: promptId,
      client_token: clientToken ?? null,
      success_url: urls?.success_url ?? null,
      cancel_url: urls?.cancel_url ?? null,
    }),
  );
}

export async function upsertPromptReview(
  promptId: string,
  body: { rating: number; text?: string | null },
): Promise<PromptReview> {
  return authFetch<PromptReview>(
    apiPath.marketplacePromptReview(promptId),
    jsonInit("PUT", body),
  );
}
