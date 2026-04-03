"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { useI18n } from "@/components/i18n/LanguageProvider";

import { HeaderPrimaryNav } from "./HeaderPrimaryNav";
import { HeaderNav } from "./HeaderNav";
import { HeaderSearch } from "./HeaderSearch";

export function Header() {
  const compactEnterThreshold = 28;
  const compactExitThreshold = 4;
  const { t } = useI18n();
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
          </div>

          <div className="border-t border-[rgba(15,23,42,0.08)] lg:hidden">
            <div className="space-y-4 px-4 pb-4 pt-4 sm:px-5">
              <HeaderSearch mobile />

              <div className="rounded-[1.25rem] border border-[rgba(15,23,42,0.08)] bg-white/72 p-2 shadow-[0_14px_28px_rgba(15,23,42,0.04)]">
                <HeaderPrimaryNav mobile />
              </div>

              <LanguageSwitcher mobile />
              <HeaderNav mobile />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
