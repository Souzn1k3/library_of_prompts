"use client";

import { useMemo } from "react";

import { getApiBaseUrl } from "@/lib/api/transport";

type TelegramAuthButtonProps = {
  label?: string;
  ariaLabel?: string;
  mode?: "login" | "link";
  nextPath?: string;
  variant?: "primary" | "secondary";
  iconOnly?: boolean;
  className?: string;
};

export function TelegramAuthButton({
  label,
  ariaLabel,
  mode = "login",
  nextPath,
  variant = "secondary",
  iconOnly = false,
  className,
}: TelegramAuthButtonProps) {
  const href = useMemo(() => {
    const apiBase = getApiBaseUrl().replace(/\/$/, "");
    const base =
      apiBase.startsWith("http://") || apiBase.startsWith("https://")
        ? apiBase
        : apiBase.startsWith("/")
          ? apiBase
          : `/${apiBase}`;
    const url = new URL(`${base}/api/v1/auth/telegram/start`, "http://local.codex");
    url.searchParams.set("mode", mode);
    if (nextPath) {
      url.searchParams.set("next", nextPath);
    }
    if (base.startsWith("http://") || base.startsWith("https://")) {
      return url.toString();
    }
    return `${url.pathname}${url.search}`;
  }, [mode, nextPath]);

  const toneClassName =
    variant === "primary"
      ? "pv-button-primary border border-[#199bd7] bg-[#199bd7] text-white hover:bg-[#1587bb]"
      : "pv-button-secondary border border-[#199bd7]/30 bg-[#199bd7]/8 text-[#0c6f99] hover:bg-[#199bd7]/12";
  const buttonClassName = iconOnly
    ? "inline-flex h-10 w-10 items-center justify-center rounded-full p-0 text-[var(--pv-text)] transition-transform duration-150 hover:scale-105 hover:text-[var(--pv-brand-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--pv-brand)]/35"
    : toneClassName;

  return (
    <a
      href={href}
      aria-label={ariaLabel ?? label ?? "Telegram"}
      title={ariaLabel ?? label ?? "Telegram"}
      className={`${buttonClassName} ${className ?? ""}`.trim()}
    >
      {iconOnly ? (
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-9 w-9"
          fill="currentColor"
        >
          <path d="M19.777 4.43c.305-.126.636.145.56.458l-2.694 11.58a.43.43 0 0 1-.643.267l-3.513-2.116-1.79 1.725a.43.43 0 0 1-.729-.298v-2.52l7.578-6.846a.215.215 0 0 0-.274-.328L8.91 12.254 5.45 11.15a.43.43 0 0 1-.028-.812l14.355-5.908Z" />
        </svg>
      ) : (
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-5 w-5 shrink-0"
          fill="currentColor"
        >
          <path d="M19.777 4.43c.305-.126.636.145.56.458l-2.694 11.58a.43.43 0 0 1-.643.267l-3.513-2.116-1.79 1.725a.43.43 0 0 1-.729-.298v-2.52l7.578-6.846a.215.215 0 0 0-.274-.328L8.91 12.254 5.45 11.15a.43.43 0 0 1-.028-.812l14.355-5.908Z" />
        </svg>
      )}
      {iconOnly ? <span className="sr-only">{ariaLabel ?? label ?? "Telegram"}</span> : label}
    </a>
  );
}
