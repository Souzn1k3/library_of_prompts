"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";

const STORAGE_KEY = "pv_onboarding_dismissed_v1";

export function OnboardingBanner() {
  const [visible, setVisible] = useState(false);
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

  if (!visible) {
    return null;
  }

  return (
    <div className="border-b border-zinc-200 bg-zinc-50">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-3 text-sm text-zinc-800 sm:flex-row sm:items-center sm:justify-between">
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
          className="shrink-0 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-900 transition hover:border-zinc-400"
        >
          {t("onboarding.dismiss")}
        </button>
      </div>
    </div>
  );
}
