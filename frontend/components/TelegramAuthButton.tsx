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
    ? "inline-flex items-center justify-center p-0 text-[#229ED9] transition-transform duration-150 hover:scale-110 hover:text-[#1b8fc5] focus-visible:outline-none"
    : toneClassName;

  return (
    <a
      href={href}
      aria-label={ariaLabel ?? label ?? "Telegram"}
      title={ariaLabel ?? label ?? "Telegram"}
      className={`${buttonClassName} ${className ?? ""}`.trim()}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className={iconOnly ? "h-11 w-11" : "h-5 w-5 shrink-0"}
        fill="currentColor"
      >
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0Zm5.895 7.58-1.97 9.291c-.148.66-.537.82-1.088.51l-3.012-2.218-1.453 1.399c-.162.16-.298.297-.61.297l.213-3.055 5.561-5.022c.242-.214-.052-.334-.373-.12l-6.873 4.327-2.96-.923c-.644-.203-.657-.644.135-.954l11.57-4.459c.538-.197 1.007.128.86.947Z" />
      </svg>
      {iconOnly ? <span className="sr-only">{ariaLabel ?? label ?? "Telegram"}</span> : label}
    </a>
  );
}
