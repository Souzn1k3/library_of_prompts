import { API_ENDPOINTS, apiPath } from "../constants/api";
import type { PurchaseResult, StoreItem, WalletRead } from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchWallet(): Promise<WalletRead> {
  return authFetch<WalletRead>(API_ENDPOINTS.wallet);
}

export async function walletCheckIn(): Promise<WalletRead> {
  return authFetch<WalletRead>(API_ENDPOINTS.walletCheckIn, {
    method: "POST",
  });
}

export async function fetchStoreItems(): Promise<StoreItem[]> {
  return authFetch<StoreItem[]>(API_ENDPOINTS.store);
}

export async function purchaseStoreItem(slug: string, clientToken?: string): Promise<PurchaseResult> {
  return authFetch<PurchaseResult>(
    apiPath.storePurchaseBySlug(slug),
    jsonInit("POST", { client_token: clientToken ?? null }),
  );
}
