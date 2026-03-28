"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";

export function HomeHeroActions() {
  const { t } = useI18n();

  return (
    <div className="flex flex-wrap gap-3">
      <Link
        href="/catalog"
        className="pv-button-primary"
      >
        {t("home.explorePrompts")}
      </Link>
      <Link
        href="/learn"
        className="pv-button-secondary"
      >
        {t("home.startLearning")}
      </Link>
    </div>
  );
}
