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
      <div className="mx-auto w-full max-w-[1280px]">
        <div className="pv-alert pv-alert-info flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-[var(--pv-text)]">{t("onboarding.welcome")}</p>
            <p className="text-sm leading-relaxed text-slate-700">
              {t("onboarding.prefix")}{" "}
              <Link href="/catalog" className="font-semibold text-[var(--pv-brand-strong)]">
                {t("onboarding.catalog")}
              </Link>
              {t("onboarding.learnPrefix")}{" "}
              <Link href="/learn" className="font-semibold text-[var(--pv-brand-strong)]">
                {t("onboarding.learnLink")}
              </Link>{" "}
              {t("onboarding.or")}{" "}
              <Link href="/signup" className="font-semibold text-[var(--pv-brand-strong)]">
                {t("onboarding.signup")}
              </Link>{" "}
              {t("onboarding.suffix")}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/catalog" className="pv-button-secondary !w-auto">
              {t("home.explorePrompts")}
            </Link>
            <button
              type="button"
              onClick={dismiss}
              className="pv-button-ghost !w-auto px-3 py-2 text-xs font-semibold text-slate-600"
            >
              {t("onboarding.dismiss")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
