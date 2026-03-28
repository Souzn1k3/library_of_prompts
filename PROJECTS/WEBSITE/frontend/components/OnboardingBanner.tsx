"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

const STORAGE_KEY = "pv_onboarding_dismissed_v1";

export function OnboardingBanner() {
  const [visible, setVisible] = useState(false);
  const { status } = useAuth();
  const { t } = useI18n();

  useEffect(() => {
    try {
      setVisible(!window.localStorage.getItem(STORAGE_KEY));
    } catch {
      setVisible(true);
    }
  }, []);

  function dismiss() {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
    setVisible(false);
  }

  if (!visible || status !== "unauthenticated") {
    return null;
  }

  return (
    <div className="px-4 pt-4 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-3 rounded-[1.5rem] border border-[var(--pv-border)] bg-white/75 px-4 py-3 text-sm text-zinc-800 shadow-[0_16px_36px_rgba(15,23,42,0.06)] sm:flex-row sm:items-center sm:justify-between">
        <p className="leading-relaxed">
          <span className="font-medium text-zinc-900">{t("onboarding.welcome")}</span>{" "}
          {t("onboarding.prefix")}{" "}
          <Link href="/catalog" className="underline">
            {t("onboarding.catalog")}
          </Link>
          {t("onboarding.learnPrefix")}{" "}
          <Link href="/learn" className="underline">
            {t("onboarding.learnLink")}
          </Link>
          {" "}{t("onboarding.or")}{" "}
          <Link href="/signup" className="underline">
            {t("onboarding.signup")}
          </Link>{" "}
          {t("onboarding.suffix")}
        </p>
        <button
          type="button"
          onClick={dismiss}
          className="shrink-0 rounded-full border border-[var(--pv-border)] bg-white px-3 py-1.5 text-xs font-semibold text-zinc-900 transition hover:border-[var(--pv-border-strong)]"
        >
          {t("onboarding.dismiss")}
        </button>
      </div>
    </div>
  );
}
