"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function HomeHeroActions({ initialAuthenticated = false }: { initialAuthenticated?: boolean }) {
  const { t } = useI18n();
  const { status } = useAuth();
  const isAuthenticated = status === "authenticated" || (status === "loading" && initialAuthenticated);

  if (isAuthenticated) {
    return (
      <div className="pv-cta-group pv-hero-actions">
        <Link href="/dashboard" className="pv-button-primary pv-hero-button-primary">
          {t("home.openDashboard")}
        </Link>
        <Link href="/catalog" className="pv-button-secondary pv-hero-button-secondary">
          {t("home.explorePrompts")}
          <span className="pv-hero-button-secondary-icon" aria-hidden="true">
            ↗
          </span>
        </Link>
      </div>
    );
  }

  return (
    <div className="pv-cta-group pv-hero-actions">
      <Link href="/signup" className="pv-button-primary pv-hero-button-primary">
        {t("home.startFree")}
      </Link>
      <Link href="/catalog" className="pv-button-secondary pv-hero-button-secondary">
        {t("home.explorePrompts")}
        <span className="pv-hero-button-secondary-icon" aria-hidden="true">
          ↗
        </span>
      </Link>
    </div>
  );
}
