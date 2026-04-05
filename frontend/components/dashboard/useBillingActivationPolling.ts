"use client";

import { useEffect } from "react";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { fetchBillingStatus } from "@/lib/client-api";
import type { BillingStatus } from "@/lib/types";

type UseBillingActivationPollingParams = {
  status: AuthStatus;
  billingQueryState: string | null;
  onBillingUpdate: (billing: BillingStatus) => void;
};

const MAX_ATTEMPTS = 12;
const POLL_INTERVAL_MS = 2500;

export function useBillingActivationPolling({
  status,
  billingQueryState,
  onBillingUpdate,
}: UseBillingActivationPollingParams): void {
  useEffect(() => {
    if (status !== "authenticated") return;
    if (billingQueryState !== "success") return;

    let attempt = 0;
    const interval = window.setInterval(() => {
      attempt += 1;
      fetchBillingStatus()
        .then((nextStatus) => {
          onBillingUpdate(nextStatus);
          const ready = nextStatus.status === "active" || nextStatus.status === "trialing";
          if (ready || attempt >= MAX_ATTEMPTS) {
            window.clearInterval(interval);
          }
        })
        .catch(() => {
          if (attempt >= MAX_ATTEMPTS) {
            window.clearInterval(interval);
          }
        });
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [billingQueryState, onBillingUpdate, status]);
}

