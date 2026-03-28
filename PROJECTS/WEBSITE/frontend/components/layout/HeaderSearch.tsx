"use client";

import { FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";

export function HeaderSearch() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const currentQuery = pathname.startsWith("/catalog") ? searchParams.get("q") ?? "" : "";
  const [query, setQuery] = useState(currentQuery);

  useEffect(() => {
    setQuery(currentQuery);
  }, [currentQuery]);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    router.push(`/catalog${trimmed ? `?q=${encodeURIComponent(trimmed)}` : ""}`);
  }

  return (
    <form
      onSubmit={onSubmit}
      className="flex w-full items-center gap-2 rounded-full border border-[var(--pv-border)] bg-white p-1 lg:min-w-[300px]"
    >
      <label htmlFor="global-search" className="sr-only">
        {t("header.searchLabel")}
      </label>
      <div className="flex min-w-0 flex-1 items-center gap-2 px-3">
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          className="h-4 w-4 shrink-0 text-zinc-400"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="8.5" cy="8.5" r="5.5" />
          <path d="m12.5 12.5 4 4" />
        </svg>
        <input
          id="global-search"
          name="q"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("header.searchPlaceholder")}
          className="w-full min-w-0 border-0 bg-transparent px-0 py-2 text-sm text-zinc-900 outline-none ring-0 placeholder:text-zinc-400 focus:ring-0"
        />
      </div>
      <button
        type="submit"
        className="rounded-full bg-[var(--pv-brand)] px-3.5 py-2 text-sm font-medium text-white transition hover:bg-[var(--pv-brand-strong)]"
      >
        {t("header.searchAction")}
      </button>
    </form>
  );
}
