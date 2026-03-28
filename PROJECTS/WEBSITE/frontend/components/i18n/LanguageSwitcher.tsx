"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { Language, TranslationKey } from "@/lib/i18n";

const languageLabelKey: Record<Language, TranslationKey> = {
  en: "lang.en",
  ru: "lang.ru",
  tt: "lang.tt",
};

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useI18n();

  return (
    <div
      className="inline-flex items-center rounded-full border border-[var(--pv-border)] bg-white/75 p-1 text-xs shadow-[0_10px_24px_rgba(15,23,42,0.06)]"
      role="group"
      aria-label={t("a11y.languageSwitcher")}
    >
      {(["en", "ru", "tt"] as const).map((langCode) => (
        <button
          key={langCode}
          type="button"
          data-testid={`lang-switch-${langCode}`}
          onClick={() => setLanguage(langCode)}
          className={`rounded-full px-2.5 py-1.5 font-semibold transition ${
            language === langCode
              ? "bg-[var(--pv-brand)] text-white shadow-[0_8px_16px_rgba(18,55,47,0.16)]"
              : "text-zinc-600 hover:text-zinc-900"
          }`}
          aria-pressed={language === langCode}
        >
          {t(languageLabelKey[langCode])}
        </button>
      ))}
    </div>
  );
}
