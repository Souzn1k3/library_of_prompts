"use client";

import { useMemo } from "react";

import { getApiBaseUrl } from "@/lib/api/transport";

type TelegramAuthButtonProps = {
  label: string;
  mode?: "login" | "link";
  nextPath?: string;
  variant?: "primary" | "secondary";
  className?: string;
};

export function TelegramAuthButton({
  label,
  mode = "login",
  nextPath,
  variant = "secondary",
  className,
}: TelegramAuthButtonProps) {
  const href = useMemo(() => {
    const url = new URL("/api/v1/auth/telegram/start", getApiBaseUrl());
    url.searchParams.set("mode", mode);
    if (nextPath) {
      url.searchParams.set("next", nextPath);
    }
    return url.toString();
  }, [mode, nextPath]);

  const toneClassName =
    variant === "primary"
      ? "pv-button-primary border border-[#199bd7] bg-[#199bd7] text-white hover:bg-[#1587bb]"
      : "pv-button-secondary border border-[#199bd7]/30 bg-[#199bd7]/8 text-[#0c6f99] hover:bg-[#199bd7]/12";

  return (
    <a href={href} className={`${toneClassName} ${className ?? ""}`.trim()}>
      {label}
    </a>
  );
}
