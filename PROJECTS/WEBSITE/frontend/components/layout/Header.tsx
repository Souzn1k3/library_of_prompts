"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { useI18n } from "@/components/i18n/LanguageProvider";

import { HeaderPrimaryNav } from "./HeaderPrimaryNav";
import { HeaderNav } from "./HeaderNav";
import { HeaderSearch } from "./HeaderSearch";

export function Header() {
  const compactEnterThreshold = 28;
  const compactExitThreshold = 4;
  const pathname = usePathname();
  const { t } = useI18n();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

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
    setMobileOpen(false);
  }, [pathname]);

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
              <HeaderNav />
            </div>

            <button
              type="button"
              onClick={() => setMobileOpen((value) => !value)}
              aria-expanded={mobileOpen}
              aria-label={mobileOpen ? t("header.closeNavigation") : t("header.openNavigation")}
              className={`pv-header-burger lg:hidden ${mobileOpen ? "pv-header-burger-active" : ""}`}
            >
              <span />
              <span />
              <span />
            </button>
          </div>

          <div
            className={`overflow-hidden border-t border-transparent transition-[max-height,opacity,border-color] duration-200 lg:hidden ${
              mobileOpen
                ? "max-h-[38rem] border-[rgba(15,23,42,0.08)] opacity-100"
                : "max-h-0 opacity-0"
            }`}
          >
            <div className="space-y-4 px-4 pb-4 pt-4 sm:px-5">
              <HeaderSearch mobile onSearch={() => setMobileOpen(false)} />

              <div className="rounded-[1.25rem] border border-[rgba(15,23,42,0.08)] bg-white/72 p-2 shadow-[0_14px_28px_rgba(15,23,42,0.04)]">
                <HeaderPrimaryNav mobile onNavigate={() => setMobileOpen(false)} />
              </div>

              <LanguageSwitcher mobile />
              <HeaderNav mobile onNavigate={() => setMobileOpen(false)} />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
