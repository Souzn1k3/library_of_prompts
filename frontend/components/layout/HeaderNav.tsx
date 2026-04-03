"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { getAccountMenuItems, isAccountMenuItemActive } from "@/lib/navigation";

type HeaderNavProps = {
  mobile?: boolean;
  onNavigate?: () => void;
};

function getInitials(value: string) {
  const parts = value
    .split(/\s+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "PV";
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function HeaderNav({ mobile = false, onNavigate }: HeaderNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { status, user, logout } = useAuth();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const menuItems = getAccountMenuItems();
  const accountActive = isAccountMenuItemActive(pathname);
  const userLabel = user?.display_name?.trim() || t("nav.profile");
  const userInitials = getInitials(userLabel);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  async function handleLogout() {
    await logout();
    setOpen(false);
    onNavigate?.();
    router.push("/");
    router.refresh();
  }

  if (status === "loading") {
    return mobile ? (
      <div
        className="min-h-[8.5rem] rounded-[1.25rem] border border-[rgba(15,23,42,0.08)] bg-white/72"
        aria-hidden
      />
    ) : (
      <span className="hidden min-w-24 lg:inline-block" aria-hidden />
    );
  }

  if (status === "authenticated") {
    if (mobile) {
      return (
        <div className="rounded-[1.25rem] border border-[rgba(15,23,42,0.08)] bg-white/72 p-3.5 shadow-[0_14px_28px_rgba(15,23,42,0.04)]">
          <div className="flex items-center gap-3">
            <span className="pv-header-avatar pv-header-avatar-lg">{userInitials}</span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-zinc-950">{userLabel}</p>
            </div>
          </div>

          <div className="mt-3 grid gap-1">
            {menuItems.map((item) => {
              const active = item.isActive(pathname);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={onNavigate}
                  className={`pv-header-mobile-link ${active ? "pv-header-mobile-link-active" : ""}`}
                >
                  {t(item.labelKey)}
                </Link>
              );
            })}
          </div>

          <button type="button" onClick={handleLogout} className="pv-header-mobile-logout">
            {t("nav.logout")}
          </button>
        </div>
      );
    }

    return (
      <div ref={menuRef} className="pv-header-account-wrap relative">
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-haspopup="menu"
          aria-label={t("header.accountMenu")}
          className={`pv-header-user-trigger ${
            open || accountActive ? "pv-header-user-trigger-active" : ""
          }`}
        >
          <span className="pv-header-avatar">{userInitials}</span>
          <span className="max-w-[10rem] truncate text-[0.92rem] font-semibold text-zinc-950 xl:max-w-[12rem]">
            {userLabel}
          </span>
          <svg
            aria-hidden="true"
            viewBox="0 0 20 20"
            className={`h-4 w-4 text-zinc-400 transition ${open ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m5.5 8 4.5 4 4.5-4" />
          </svg>
        </button>

        {open ? (
          <div className="pv-header-dropdown absolute right-0 top-full mt-2.5 w-[15rem]">
            <div className="grid gap-1">
              {menuItems.map((item) => {
                const active = item.isActive(pathname);
                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    onClick={() => {
                      setOpen(false);
                      onNavigate?.();
                    }}
                    className={`pv-header-menu-link ${active ? "pv-header-menu-link-active" : ""}`}
                  >
                    {t(item.labelKey)}
                  </Link>
                );
              })}
            </div>

            <div className="mt-2 border-t border-[rgba(15,23,42,0.08)] pt-2">
              <button type="button" onClick={handleLogout} className="pv-header-menu-link w-full">
                {t("nav.logout")}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  if (mobile) {
    return (
      <Link
        href="/login"
        onClick={onNavigate}
        className="pv-header-ghost-button w-full justify-center"
      >
        {t("nav.login")}
      </Link>
    );
  }

  return (
    <Link href="/login" className="pv-header-ghost-button">
      {t("nav.login")}
    </Link>
  );
}
