"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  DEFAULT_LANGUAGE,
  LANGUAGE_COOKIE_KEY,
  LANGUAGE_COOKIE_MAX_AGE_SECONDS,
  LANGUAGE_STORAGE_KEY,
  formatTranslation,
  type Language,
  type TranslationKey,
  extractLanguageFromCookie,
  normalizeLanguage,
} from "@/lib/i18n";

type LanguageContextValue = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

function detectPreferredLanguage(): Language {
  if (typeof window === "undefined") {
    return DEFAULT_LANGUAGE;
  }

  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored) {
      return normalizeLanguage(stored);
    }
  } catch {
    /* ignore */
  }

  const cookieLanguage = extractLanguageFromCookie(document.cookie);
  if (cookieLanguage) {
    return cookieLanguage;
  }

  return normalizeLanguage(window.navigator.language);
}

function persistLanguage(language: Language): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    /* ignore */
  }
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${LANGUAGE_COOKIE_KEY}=${encodeURIComponent(language)}; Path=/; Max-Age=${LANGUAGE_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax${secure}`;
}

export function LanguageProvider({
  children,
  initialLanguage,
}: {
  children: React.ReactNode;
  initialLanguage?: Language;
}) {
  const router = useRouter();
  // Hydration-safe: first server/client render uses the same language.
  const [language, setLanguageState] = useState<Language>(() =>
    normalizeLanguage(initialLanguage ?? DEFAULT_LANGUAGE),
  );
  const mountedRef = useRef(false);

  useEffect(() => {
    const detected = detectPreferredLanguage();
    setLanguageState((current) => (current === detected ? current : detected));
  }, []);

  const setLanguage = useCallback((nextLanguage: Language) => {
    const normalized = normalizeLanguage(nextLanguage);
    document.documentElement.lang = normalized;
    persistLanguage(normalized);
    setLanguageState((current) => (current === normalized ? current : normalized));
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    persistLanguage(language);
  }, [language]);

  useEffect(() => {
    if (!mountedRef.current) {
      mountedRef.current = true;
      return;
    }
    router.refresh();
  }, [language, router]);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key !== LANGUAGE_STORAGE_KEY) return;
      const next = normalizeLanguage(event.newValue);
      setLanguageState((current) => (current === next ? current : next));
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value = useMemo<LanguageContextValue>(
    () => ({
      language,
      setLanguage,
      t: (key, params) => formatTranslation(language, key, params),
    }),
    [language, setLanguage],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useI18n must be used inside LanguageProvider");
  }
  return ctx;
}
