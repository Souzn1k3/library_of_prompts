"use client";

import { useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { createBillingPortalSession } from "@/lib/client-api";

export function useBillingPortal(errorKey = "plans.portalFailed") {
  const { t } = useI18n();
  const [portalPending, setPortalPending] = useState(false);
  const [portalError, setPortalError] = useState<string | null>(null);

  async function openPortal() {
    setPortalError(null);
    setPortalPending(true);
    try {
      const session = await createBillingPortalSession();
      window.location.href = session.url;
    } catch (error) {
      setPortalError(error instanceof Error ? error.message : t(errorKey));
    } finally {
      setPortalPending(false);
    }
  }

  function clearPortalError() {
    setPortalError(null);
  }

  return {
    portalError,
    portalPending,
    openPortal,
    clearPortalError,
  };
}
