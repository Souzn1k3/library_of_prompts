"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function HomeHeroActions() {
  const { status } = useAuth();
  const { t } = useI18n();

  return (
    <div className="flex flex-wrap gap-3">
      <Link
        href="/catalog"
        className="inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800"
      >
        {t("home.browseCatalog")}
      </Link>
      <Link
        href="/learn"
        className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
      >
        {t("home.startLearning")}
      </Link>
      <Link
        href="/catalog?sort=trending"
        className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
      >
        {t("home.trendingPrompts")}
      </Link>
      {status === "authenticated" ? (
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
        >
          {t("onboardingWizard.goDashboard")}
        </Link>
      ) : null}
      {status === "unauthenticated" ? (
        <Link
          href="/signup"
          className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
        >
          {t("home.createAccount")}
        </Link>
      ) : null}
    </div>
  );
}
