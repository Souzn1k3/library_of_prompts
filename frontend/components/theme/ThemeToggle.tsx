"use client";

import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";

const THEME_STORAGE_KEY = "pv-theme";

type ThemeMode = "light" | "dark";

function readThemeFromDom(): ThemeMode {
  if (typeof document === "undefined") {
    return "light";
  }

  const value = document.documentElement.getAttribute("data-theme");
  return value === "dark" ? "dark" : "light";
}

function resolveTheme(): ThemeMode {
  if (typeof window === "undefined") {
    return "light";
  }

  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "dark" || stored === "light") {
    return stored;
  }

  return "light";
}

function applyTheme(theme: ThemeMode) {
  if (typeof document === "undefined") {
    return;
  }
  document.documentElement.setAttribute("data-theme", theme);
}

type ThemeToggleProps = {
  mobile?: boolean;
};

function ThemeGlyph({ theme }: { theme: ThemeMode }) {
  if (theme === "dark") {
    return (
      <svg
        aria-hidden="true"
        viewBox="0 0 20 20"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M13.75 2.5a7.4 7.4 0 1 0 3.75 13.76A8.1 8.1 0 0 1 13.75 2.5Z" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="10" cy="10" r="3.2" />
      <path d="M10 1.8v2.2M10 16v2.2M18.2 10H16M4 10H1.8M15.8 4.2l-1.5 1.5M5.7 14.3l-1.5 1.5M15.8 15.8l-1.5-1.5M5.7 5.7 4.2 4.2" />
    </svg>
  );
}

export function ThemeToggle({ mobile = false }: ThemeToggleProps) {
  const { t } = useI18n();
  const [theme, setTheme] = useState<ThemeMode>("light");

  useEffect(() => {
    const current = resolveTheme();
    setTheme(current);
    applyTheme(current);
  }, []);

  useEffect(() => {
    const onThemeChange = (event: Event) => {
      const customEvent = event as CustomEvent<ThemeMode>;
      const nextTheme = customEvent.detail === "dark" ? "dark" : "light";
      setTheme(nextTheme);
      applyTheme(nextTheme);
    };

    const onStorage = (event: StorageEvent) => {
      if (event.key !== THEME_STORAGE_KEY || !event.newValue) {
        return;
      }
      if (event.newValue === "dark" || event.newValue === "light") {
        setTheme(event.newValue);
        applyTheme(event.newValue);
      }
    };

    window.addEventListener("pv-theme-change", onThemeChange as EventListener);
    window.addEventListener("storage", onStorage);

    return () => {
      window.removeEventListener("pv-theme-change", onThemeChange as EventListener);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  function toggleTheme() {
    const current = readThemeFromDom();
    const nextTheme: ThemeMode = current === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    applyTheme(nextTheme);
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    window.dispatchEvent(new CustomEvent<ThemeMode>("pv-theme-change", { detail: nextTheme }));
  }

  const label = theme === "dark" ? t("theme.dark") : t("theme.light");
  const actionLabel = theme === "dark" ? t("theme.toggleToLight") : t("theme.toggleToDark");

  if (mobile) {
    return (
      <button
        type="button"
        onClick={toggleTheme}
        className="inline-flex w-full items-center justify-between rounded-[1rem] border border-[rgba(15,23,42,0.08)] bg-white/72 px-4 py-3 text-sm font-semibold text-zinc-900"
        aria-label={actionLabel}
      >
        <span className="text-zinc-600">{t("a11y.themeSwitcher")}</span>
        <span className="inline-flex items-center gap-2">
          <ThemeGlyph theme={theme} />
          <span>{label}</span>
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="pv-header-ghost-button min-w-[5.75rem] justify-between gap-2 px-3"
      aria-label={actionLabel}
    >
      <span className="text-[0.82rem] font-semibold">{label}</span>
      <ThemeGlyph theme={theme} />
    </button>
  );
}
