"use client";

import { useEffect, useRef, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { Language, TranslationKey } from "@/lib/i18n";

const languageLabelKey: Record<Language, TranslationKey> = {
  en: "lang.en",
  ru: "lang.ru",
  tt: "lang.tt",
};

type LanguageSwitcherProps = {
  mobile?: boolean;
};

export function LanguageSwitcher({ mobile = false }: LanguageSwitcherProps) {
  const { language, setLanguage, t } = useI18n();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  if (mobile) {
    return (
      <div className="rounded-[0.9rem] border border-[var(--pv-border)] bg-white p-3.5">
        <p className="text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-zinc-500">
          {t("a11y.languageSwitcher")}
        </p>

        <div
          className="mt-3 inline-flex rounded-full border border-[var(--pv-border)] bg-white p-1"
          role="group"
          aria-label={t("a11y.languageSwitcher")}
        >
          {(["en", "ru", "tt"] as const).map((langCode) => (
            <button
              key={langCode}
              type="button"
              data-testid={`lang-switch-${langCode}`}
              onClick={() => setLanguage(langCode)}
              className={`min-h-[2.5rem] rounded-full px-3.5 text-sm font-semibold transition ${
                language === langCode
                  ? "bg-[var(--pv-brand)] text-white"
                  : "text-zinc-500 hover:text-zinc-950"
              }`}
              aria-pressed={language === langCode}
            >
              {t(languageLabelKey[langCode])}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={t("a11y.languageSwitcher")}
        className="pv-header-ghost-button min-w-[4.75rem] justify-between gap-2 px-3"
      >
        <span className="text-[0.82rem] font-semibold">{t(languageLabelKey[language])}</span>
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          className={`h-4 w-4 text-zinc-400 transition ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m5.5 8 4.5 4 4.5-4" />
        </svg>
      </button>

      {open ? (
        <div className="pv-header-dropdown absolute right-0 top-full mt-2.5 w-[7rem] p-1.5">
          {(["en", "ru", "tt"] as const).map((langCode) => (
            <button
              key={langCode}
              type="button"
              data-testid={`lang-switch-${langCode}`}
              onClick={() => {
                setLanguage(langCode);
                setOpen(false);
              }}
              className={`pv-header-menu-link w-full ${
                language === langCode ? "pv-header-menu-link-active" : ""
              }`}
              aria-pressed={language === langCode}
            >
              {t(languageLabelKey[langCode])}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
