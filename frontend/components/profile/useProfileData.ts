"use client";

import { useCallback, useEffect, useState } from "react";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { ApiRequestError } from "@/lib/api";
import {
  fetchBillingStatus,
  fetchMarketplaceOverview,
  fetchOnboardingProfile,
  fetchWallet,
} from "@/lib/client-api";
import type {
  BillingStatus,
  MarketplaceOverview,
  OnboardingProfile,
  WalletRead,
} from "@/lib/types";

type UseProfileDataArgs = {
  status: AuthStatus;
  isAuthenticated: boolean;
  marketplaceUnavailableMessage: string;
};

type UseProfileDataResult = {
  overview: MarketplaceOverview | null;
  billing: BillingStatus | null;
  onboardingProfile: OnboardingProfile | null;
  wallet: WalletRead | null;
  error: string | null;
  lastMarketplaceSyncAt: string | null;
  reload: () => void;
};

export function useProfileData({
  status,
  isAuthenticated,
  marketplaceUnavailableMessage,
}: UseProfileDataArgs): UseProfileDataResult {
  const [overview, setOverview] = useState<MarketplaceOverview | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [onboardingProfile, setOnboardingProfile] = useState<OnboardingProfile | null>(null);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastMarketplaceSyncAt, setLastMarketplaceSyncAt] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    if (status !== "authenticated" || !isAuthenticated) {
      setOverview(null);
      setBilling(null);
      setOnboardingProfile(null);
      setWallet(null);
      setLastMarketplaceSyncAt(null);
      setError(null);
      return;
    }

    let cancelled = false;

    Promise.allSettled([
      fetchMarketplaceOverview(),
      fetchBillingStatus(),
      fetchOnboardingProfile(),
      fetchWallet(),
    ])
      .then((results) => {
        if (cancelled) {
          return;
        }

        const [overviewResult, billingResult, onboardingResult, walletResult] = results;

        if (overviewResult.status === "fulfilled") {
          setOverview(overviewResult.value);
        }
        if (billingResult.status === "fulfilled") {
          setBilling(billingResult.value);
        }
        if (onboardingResult.status === "fulfilled") {
          setOnboardingProfile(onboardingResult.value);
        }
        if (walletResult.status === "fulfilled") {
          setWallet(walletResult.value);
        } else {
          setWallet(null);
        }

        if (
          overviewResult.status === "fulfilled" ||
          billingResult.status === "fulfilled" ||
          onboardingResult.status === "fulfilled"
        ) {
          setLastMarketplaceSyncAt(new Date().toISOString());
        }

        const firstError = [overviewResult, billingResult].find(
          (result) => result.status === "rejected",
        );
        if (!firstError || firstError.status !== "rejected") {
          setError(null);
          return;
        }

        setError(
          firstError.reason instanceof ApiRequestError
            ? firstError.reason.message
            : marketplaceUnavailableMessage,
        );
      })
      .catch(() => {
        if (!cancelled) {
          setError(marketplaceUnavailableMessage);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, marketplaceUnavailableMessage, reloadToken, status]);

  return {
    overview,
    billing,
    onboardingProfile,
    wallet,
    error,
    lastMarketplaceSyncAt,
    reload,
  };
}
