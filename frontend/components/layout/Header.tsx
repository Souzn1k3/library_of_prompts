"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

import { HeaderPrimaryNav } from "./HeaderPrimaryNav";
import { HeaderNav } from "./HeaderNav";
import { HeaderSearch } from "./HeaderSearch";

export function Header() {
  const compactEnterThreshold = 28;
  const compactExitThreshold = 4;
  const { t } = useI18n();
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    function handleScroll() {
      setIsScrolled((current) => {
        const scrollY = window.scrollY;

        if (current) {
          return scrollY > compactExitThreshold;
        }

        return scrollY > compactEnterThreshold;
      });
    }

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [compactEnterThreshold, compactExitThreshold]);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!isMobileMenuOpen) {
      return;
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsMobileMenuOpen(false);
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isMobileMenuOpen]);

  return (
    <>
      <header className="lg:hidden">
        <div className={`pv-site-header ${isScrolled ? "pv-site-header-compact" : ""}`}>
          <div className="pv-site-header-top">
            <Link href="/" className="pv-site-brand" aria-label={t("brand.name")}>
              <span className="pv-site-brand-mark">PV</span>
              <span className="pv-site-brand-copy">
                <span className="pv-site-brand-title">{t("brand.name")}</span>
                <span className="pv-site-brand-subtitle">{t("home.kicker")}</span>
              </span>
            </Link>

            <button
              type="button"
              className="pv-header-mobile-trigger inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-[1rem] border border-[rgba(15,23,42,0.12)] bg-white/86 text-zinc-700 transition hover:text-zinc-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]/35"
              aria-controls="mobile-navigation-panel"
              aria-expanded={isMobileMenuOpen}
              aria-label={isMobileMenuOpen ? t("header.closeMenu") : t("header.openMenu")}
              onClick={() => setIsMobileMenuOpen((value) => !value)}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 20 20"
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {isMobileMenuOpen ? (
                  <>
                    <path d="m5 5 10 10" />
                    <path d="M15 5 5 15" />
                  </>
                ) : (
                  <>
                    <path d="M3.5 5.75h13" />
                    <path d="M3.5 10h13" />
                    <path d="M3.5 14.25h13" />
                  </>
                )}
              </svg>
            </button>
          </div>

          {isMobileMenuOpen ? (
            <div id="mobile-navigation-panel" className="pv-site-header-mobile">
              <div className="space-y-4">
                <HeaderSearch mobile onSearch={() => setIsMobileMenuOpen(false)} />

                <div className="rounded-[1.35rem] border border-[rgba(15,23,42,0.08)] bg-white/78 p-2 shadow-[0_16px_30px_rgba(15,23,42,0.05)]">
                  <HeaderPrimaryNav mobile onNavigate={() => setIsMobileMenuOpen(false)} />
                </div>

                <LanguageSwitcher mobile />
                <ThemeToggle mobile />
                <HeaderNav mobile onNavigate={() => setIsMobileMenuOpen(false)} />
              </div>
            </div>
          ) : null}
        </div>
      </header>

      <aside className={`pv-shell-sidebar hidden lg:flex ${isScrolled ? "pv-shell-sidebar-compact" : ""}`}>
        <div className="space-y-5">
          <Link href="/" className="pv-site-brand" aria-label={t("brand.name")}>
            <span className="pv-site-brand-mark">PV</span>
            <span className="pv-site-brand-copy">
              <span className="pv-site-brand-title">{t("brand.name")}</span>
              <span className="pv-site-brand-subtitle">{t("home.kicker")}</span>
            </span>
          </Link>

          <div className="pv-shell-sidebar-search">
            <HeaderSearch />
          </div>

          <div className="pv-shell-sidebar-nav">
            <HeaderPrimaryNav mobile />
          </div>
        </div>

        <div className="mt-auto space-y-3">
          <div className="grid gap-2">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
          <HeaderNav />
        </div>
      </aside>
    </>
  );
}
