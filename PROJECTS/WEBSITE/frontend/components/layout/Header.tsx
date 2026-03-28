import Link from "next/link";
import type { ReactNode } from "react";

import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { T } from "@/components/i18n/T";

import { HeaderNav } from "./HeaderNav";
import { HeaderSearch } from "./HeaderSearch";

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--pv-border)] bg-[rgba(247,246,242,0.9)] backdrop-blur px-4 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1280px] flex-col gap-3 py-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:gap-6">
          <Link href="/" className="shrink-0 text-lg font-extrabold tracking-[-0.04em] text-zinc-950 sm:text-xl">
            <T k="brand.name" />
          </Link>

          <nav className="flex flex-wrap gap-1.5 text-sm text-zinc-700">
            <HeaderLink href="/catalog" label={<T k="nav.catalog" />} />
            <HeaderLink href="/learn" label={<T k="nav.learn" />} />
            <HeaderLink href="/missions" label={<T k="nav.missions" />} />
            <HeaderLink href="/pricing" label={<T k="nav.plans" />} />
          </nav>
        </div>

        <div className="flex flex-col gap-3 xl:min-w-[440px] xl:max-w-[560px] xl:flex-1 xl:items-end">
          <div className="flex flex-wrap items-center justify-end gap-2.5">
            <LanguageSwitcher />
            <HeaderNav />
          </div>
          <div className="w-full">
            <HeaderSearch />
          </div>
        </div>
      </div>
    </header>
  );
}

function HeaderLink({ href, label }: { href: string; label: ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center rounded-full px-3 py-1.5 font-medium transition hover:bg-white hover:text-zinc-950"
    >
      {label}
    </Link>
  );
}
