import Link from "next/link";

import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { T } from "@/components/i18n/T";

import { HeaderNav } from "./HeaderNav";

export function Header() {
  return (
    <header className="border-b border-zinc-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
        <Link href="/" className="text-sm font-semibold tracking-tight text-zinc-900">
          <T k="brand.name" />
        </Link>
        <nav className="flex items-center gap-5 text-sm text-zinc-600 sm:gap-6">
          <Link href="/catalog" className="transition hover:text-zinc-900">
            <T k="nav.catalog" />
          </Link>
          <Link href="/learn" className="transition hover:text-zinc-900">
            <T k="nav.learn" />
          </Link>
          <Link href="/plans" className="hidden transition hover:text-zinc-900 sm:inline">
            <T k="nav.plans" />
          </Link>
          <span className="hidden h-4 w-px bg-zinc-200 sm:block" aria-hidden />
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <HeaderNav />
          </div>
        </nav>
      </div>
    </header>
  );
}
