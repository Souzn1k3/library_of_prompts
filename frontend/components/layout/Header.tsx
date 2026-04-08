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
    <header className="sticky top-0 z-50 px-4 pt-3 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-[1280px]">
        <div className={`pv-header-shell ${isScrolled ? "pv-header-shell-scrolled" : ""}`}>
          <div
            className={`flex items-center gap-3 px-4 transition-[min-height,padding] duration-200 sm:px-5 lg:px-6 ${
              isScrolled ? "min-h-[4.2rem]" : "min-h-[4.7rem]"
            }`}
          >
            <div className="flex min-w-0 flex-1 items-center gap-4 lg:gap-6">
              <Link href="/" className="pv-header-brand whitespace-nowrap">
                {t("brand.name")}
              </Link>

              <div className="hidden min-w-0 lg:flex lg:flex-1">
                <HeaderPrimaryNav />
              </div>
            </div>

            <div className="hidden shrink-0 xl:flex xl:justify-center xl:overflow-visible">
              <HeaderSearch />
            </div>

            <div className="hidden shrink-0 items-center justify-end gap-2 lg:flex">
              <LanguageSwitcher />
              <ThemeToggle />
              <HeaderNav />
            </div>

            <button
              type="button"
              className="pv-header-ghost-button pv-header-mobile-trigger inline-flex h-10 w-10 shrink-0 items-center justify-center px-0 lg:hidden"
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
            <div id="mobile-navigation-panel" className="border-t border-[rgba(15,23,42,0.08)] lg:hidden">
              <div className="space-y-4 px-4 pb-4 pt-4 sm:px-5">
                <HeaderSearch mobile onSearch={() => setIsMobileMenuOpen(false)} />

                <div className="pv-card-muted p-2">
                  <HeaderPrimaryNav mobile onNavigate={() => setIsMobileMenuOpen(false)} />
                </div>

                <LanguageSwitcher mobile />
                <ThemeToggle mobile />
                <HeaderNav mobile onNavigate={() => setIsMobileMenuOpen(false)} />
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
