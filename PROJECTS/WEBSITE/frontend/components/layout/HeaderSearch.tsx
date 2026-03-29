"use client";

import { FormEvent, useEffect, useId, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";

type HeaderSearchProps = {
  mobile?: boolean;
  onSearch?: () => void;
};

export function HeaderSearch({ mobile = false, onSearch }: HeaderSearchProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const currentQuery = pathname.startsWith("/catalog") ? searchParams.get("q") ?? "" : "";
  const [query, setQuery] = useState(currentQuery);
  const hasQuery = query.trim().length > 0;

  useEffect(() => {
    setQuery(currentQuery);
  }, [currentQuery]);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    router.push(`/catalog${trimmed ? `?q=${encodeURIComponent(trimmed)}` : ""}`);
    onSearch?.();
  }

  return (
    <form
      onSubmit={onSubmit}
      onClick={(event) => {
        const target = event.target as HTMLElement;
        if (target.closest("button")) return;
        inputRef.current?.focus();
      }}
      className={`pv-header-search ${mobile ? "pv-header-search-mobile" : "pv-header-search-desktop"} ${
        !mobile && hasQuery ? "pv-header-search-expanded" : ""
      }`}
    >
      <label htmlFor={inputId} className="sr-only">
        {t("header.searchLabel")}
      </label>
      <label htmlFor={inputId} className="flex min-w-0 flex-1 cursor-text items-center gap-2.5 px-1">
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
          ref={inputRef}
          id={inputId}
          name="q"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("header.searchPlaceholder")}
          className="w-full min-w-0 border-0 bg-transparent px-0 py-2 text-[0.94rem] leading-[1.35] text-zinc-950 outline-none ring-0 placeholder:text-zinc-400 focus:ring-0"
        />
      </label>
      <button
        type="submit"
        className="pv-header-search-button"
        aria-label={t("header.searchAction")}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M4.5 10h9" />
          <path d="m10.5 6 4 4-4 4" />
        </svg>
      </button>
    </form>
  );
}
