"use client";

import Link from "next/link";
import { useEffect } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useI18n();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="pv-alert pv-alert-error space-y-4 p-6 text-red-950">
      <h1 className="text-lg font-semibold">{t("errorBoundary.title")}</h1>
      <p className="text-sm leading-relaxed">
        {t("errorBoundary.body")}
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="pv-button-primary !w-auto"
        >
          {t("errorBoundary.tryAgain")}
        </button>
        <Link
          href="/"
          className="pv-button-secondary !w-auto"
        >
          {t("errorBoundary.home")}
        </Link>
      </div>
    </div>
  );
}
