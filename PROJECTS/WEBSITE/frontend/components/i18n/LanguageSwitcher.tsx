"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  return (
    <div className="inline-flex items-center rounded-md border border-zinc-300 bg-white p-0.5 text-xs">
      <button
        type="button"
        onClick={() => setLanguage("ru")}
        className={`rounded px-2 py-1 transition ${
          language === "ru" ? "bg-zinc-900 text-white" : "text-zinc-600 hover:text-zinc-900"
        }`}
        aria-pressed={language === "ru"}
      >
        {t("lang.ru")}
      </button>
      <button
        type="button"
        onClick={() => setLanguage("en")}
        className={`rounded px-2 py-1 transition ${
          language === "en" ? "bg-zinc-900 text-white" : "text-zinc-600 hover:text-zinc-900"
        }`}
        aria-pressed={language === "en"}
      >
        {t("lang.en")}
      </button>
    </div>
  );
}
