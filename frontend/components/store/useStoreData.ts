"use client";

import { useCallback, useEffect, useState } from "react";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { ApiRequestError } from "@/lib/api";
import {
  STORE_SUCCESS_CLEAR_TIMEOUT_MS,
} from "@/lib/constants/economy-ui";
import {
  fetchStoreItems,
  fetchWallet,
  purchaseStoreItem,
} from "@/lib/client-api";
import { sortStoreItems } from "@/lib/economy";
import type { PurchaseResult, StoreItem, WalletRead } from "@/lib/types";

type UseStoreDataArgs = {
  status: AuthStatus;
  loadFailedMessage: string;
  purchaseFailedMessage: string;
};

type UseStoreDataResult = {
  items: StoreItem[];
  wallet: WalletRead | null;
  loading: boolean;
  error: string | null;
  purchasing: string | null;
  success: PurchaseResult | null;
  purchase: (item: StoreItem) => Promise<void>;
};

export function useStoreData({
  status,
  loadFailedMessage,
  purchaseFailedMessage,
}: UseStoreDataArgs): UseStoreDataResult {
  const [items, setItems] = useState<StoreItem[]>([]);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [purchasing, setPurchasing] = useState<string | null>(null);
  const [success, setSuccess] = useState<PurchaseResult | null>(null);

  useEffect(() => {
    if (status !== "authenticated") {
      setLoading(status === "loading");
      setItems([]);
      setWallet(null);
      setError(null);
      setPurchasing(null);
      setSuccess(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.allSettled([fetchStoreItems(), fetchWallet()])
      .then(([itemsResult, walletResult]) => {
        if (cancelled) {
          return;
        }
        let localError: string | null = null;
        if (itemsResult.status === "fulfilled") {
          setItems(sortStoreItems(itemsResult.value));
        } else {
          localError = loadFailedMessage;
        }
        if (walletResult.status === "fulfilled") {
          setWallet(walletResult.value);
        }
        setError(localError);
      })
      .catch((requestError) => {
        if (cancelled) {
          return;
        }
        setError(requestError instanceof ApiRequestError ? requestError.message : purchaseFailedMessage);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [loadFailedMessage, purchaseFailedMessage, status]);

  useEffect(() => {
    if (!success) {
      return;
    }
    const timeoutId = window.setTimeout(() => setSuccess(null), STORE_SUCCESS_CLEAR_TIMEOUT_MS);
    return () => window.clearTimeout(timeoutId);
  }, [success]);

  const purchase = useCallback(
    async (item: StoreItem) => {
      const clientToken =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `${item.slug}-${Date.now()}`;
      setPurchasing(item.slug);
      setSuccess(null);
      try {
        const result = await purchaseStoreItem(item.slug, clientToken);
        const refreshedItems = await fetchStoreItems();
        setWallet(result.wallet);
        setItems(sortStoreItems(refreshedItems));
        setError(null);
        setSuccess(result);
      } catch (requestError) {
        setError(requestError instanceof ApiRequestError ? requestError.message : purchaseFailedMessage);
      } finally {
        setPurchasing(null);
      }
    },
    [purchaseFailedMessage],
  );

  return {
    items,
    wallet,
    loading,
    error,
    purchasing,
    success,
    purchase,
  };
}
