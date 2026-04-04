"use client";

import { useCallback, useEffect, useState } from "react";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { ApiRequestError } from "@/lib/api";
import { fetchStoreItems, fetchWallet, walletCheckIn } from "@/lib/client-api";
import { buildClientEconomyAction } from "@/lib/economy";
import type { EconomyAction, StoreItem, WalletRead } from "@/lib/types";

type UseWalletDataArgs = {
  status: AuthStatus;
  genericErrorMessage: string;
};

type UseWalletDataResult = {
  wallet: WalletRead | null;
  items: StoreItem[];
  error: string | null;
  loading: boolean;
  checkinPending: boolean;
  checkinFeedback: EconomyAction | null;
  reload: () => void;
  checkIn: () => Promise<void>;
};

export function useWalletData({
  status,
  genericErrorMessage,
}: UseWalletDataArgs): UseWalletDataResult {
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [items, setItems] = useState<StoreItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkinPending, setCheckinPending] = useState(false);
  const [checkinFeedback, setCheckinFeedback] = useState<EconomyAction | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    if (status !== "authenticated") {
      setLoading(status === "loading");
      setWallet(null);
      setItems([]);
      setError(null);
      setCheckinFeedback(null);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all([fetchWallet(), fetchStoreItems()])
      .then(([walletData, storeItems]) => {
        if (cancelled) {
          return;
        }
        setWallet(walletData);
        setItems(storeItems);
        setError(null);
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }
        setWallet(null);
        setItems([]);
        setError(err instanceof ApiRequestError ? err.message : genericErrorMessage);
      })
      .finally(() => {
        if (cancelled) {
          return;
        }
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [genericErrorMessage, reloadToken, status]);

  const checkIn = useCallback(async () => {
    if (status !== "authenticated") {
      return;
    }

    setCheckinPending(true);
    try {
      const previousBalance = wallet?.balance ?? 0;
      const [walletData, storeItems] = await Promise.all([walletCheckIn(), fetchStoreItems()]);
      setWallet(walletData);
      setItems(storeItems);
      setError(null);
      setCheckinFeedback(
        buildClientEconomyAction({
          balanceDelta: walletData.balance - previousBalance,
          items: storeItems,
          previousBalance,
        }),
      );
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : genericErrorMessage);
      setCheckinFeedback(null);
    } finally {
      setCheckinPending(false);
    }
  }, [genericErrorMessage, status, wallet?.balance]);

  return {
    wallet,
    items,
    error,
    loading,
    checkinPending,
    checkinFeedback,
    reload,
    checkIn,
  };
}
