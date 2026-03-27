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
    <div className="space-y-4 rounded-lg border border-red-200 bg-red-50 p-6 text-red-950">
      <h1 className="text-lg font-semibold">{t("errorBoundary.title")}</h1>
      <p className="text-sm leading-relaxed">
        {t("errorBoundary.body")}
      </p>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="rounded-md bg-red-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-800"
        >
          {t("errorBoundary.tryAgain")}
        </button>
        <Link
          href="/"
          className="inline-flex items-center rounded-md border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-950 transition hover:border-red-400"
        >
          {t("errorBoundary.home")}
        </Link>
      </div>
    </div>
  );
}
