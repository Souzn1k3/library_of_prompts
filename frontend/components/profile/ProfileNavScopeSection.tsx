"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { APP_ROUTES } from "@/lib/constants/routes";

export function ProfileNavScopeSection() {
  const { t } = useI18n();

  return (
    <section className="pv-panel px-6 py-5 sm:px-7">
      <p className="pv-kicker">{t("profile.navTreeTitle")}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-zinc-700">
        <Link href={APP_ROUTES.dashboard} className="pv-chip">
          {t("nav.dashboard")}
        </Link>
        <span aria-hidden="true">→</span>
        <Link href={APP_ROUTES.profile} className="pv-chip-brand">
          {t("profile.title")}
        </Link>
        <span aria-hidden="true">→</span>
        <span className="pv-chip">{t("profile.marketplaceKicker")}</span>
      </div>
      <p className="mt-3 text-sm text-zinc-600">{t("profile.navTreeBody")}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="pv-card-muted p-4">
          <p className="pv-kicker">{t("profile.publicScopeTitle")}</p>
          <p className="mt-2 text-sm text-zinc-700">{t("profile.publicScopeBody")}</p>
        </div>
        <div className="pv-card-muted p-4">
          <p className="pv-kicker">{t("profile.privateScopeTitle")}</p>
          <p className="mt-2 text-sm text-zinc-700">{t("profile.privateScopeBody")}</p>
        </div>
      </div>
    </section>
  );
}
