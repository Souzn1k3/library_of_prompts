import Link from "next/link";

import { HeaderNav } from "./HeaderNav";

export function Header() {
  return (
    <header className="border-b border-zinc-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
        <Link href="/" className="text-sm font-semibold tracking-tight text-zinc-900">
          Prompts Vault
        </Link>
        <nav className="flex items-center gap-5 text-sm text-zinc-600 sm:gap-6">
          <Link href="/catalog" className="transition hover:text-zinc-900">
            Catalog
          </Link>
          <Link href="/learn" className="transition hover:text-zinc-900">
            Learn
          </Link>
          <Link href="/plans" className="hidden transition hover:text-zinc-900 sm:inline">
            Plans
          </Link>
          <span className="hidden h-4 w-px bg-zinc-200 sm:block" aria-hidden />
          <div className="flex items-center gap-4">
            <HeaderNav />
          </div>
        </nav>
      </div>
    </header>
  );
}
