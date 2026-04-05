"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { OnboardingProfile } from "@/lib/types";

type ProfileActionsPanelProps = {
  onboardingProfile: OnboardingProfile | null;
};

export function ProfileActionsPanel({ onboardingProfile }: ProfileActionsPanelProps) {
  const { t } = useI18n();

  return (
    <section className="pv-panel px-6 py-6">
      <p className="pv-kicker">{t("profile.actionsTitle")}</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <QuickLink href={APP_ROUTES.dashboard} label={t("profile.openDashboard")} />
        <QuickLink href={APP_ROUTES.wallet} label={t("profile.openWallet")} />
        <QuickLink href={APP_ROUTES.store} label={t("profile.openStore")} />
        {onboardingProfile?.needs_onboarding ? (
          <QuickLink href={APP_ROUTES.onboarding} label={t("profile.finishOnboarding")} />
        ) : null}
      </div>
    </section>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="pv-button-secondary">
      {label}
    </Link>
  );
}
