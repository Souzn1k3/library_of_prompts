"use client";

import Link from "next/link";
import type { RefObject } from "react";

import type { TranslationKey } from "@/lib/i18n";
import type { AccountMenuItem } from "@/lib/navigation";

type Translate = (key: TranslationKey) => string;

type HeaderNavAuthenticatedMobileProps = {
  userLabel: string;
  userInitials: string;
  pathname: string;
  menuItems: AccountMenuItem[];
  onNavigate?: () => void;
  onLogout: () => Promise<void>;
  t: Translate;
};

export function HeaderNavAuthenticatedMobile({
  userLabel,
  userInitials,
  pathname,
  menuItems,
  onNavigate,
  onLogout,
  t,
}: HeaderNavAuthenticatedMobileProps) {
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

      <button type="button" onClick={onLogout} className="pv-header-mobile-logout">
        {t("nav.logout")}
      </button>
    </div>
  );
}

type HeaderNavAuthenticatedDesktopProps = {
  menuRef: RefObject<HTMLDivElement | null>;
  userLabel: string;
  userInitials: string;
  pathname: string;
  menuItems: AccountMenuItem[];
  open: boolean;
  accountActive: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
  onClose: () => void;
  onLogout: () => Promise<void>;
  t: Translate;
};

export function HeaderNavAuthenticatedDesktop({
  menuRef,
  userLabel,
  userInitials,
  pathname,
  menuItems,
  open,
  accountActive,
  onToggle,
  onNavigate,
  onClose,
  onLogout,
  t,
}: HeaderNavAuthenticatedDesktopProps) {
  return (
    <div ref={menuRef} className="pv-header-account-wrap relative">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={t("header.accountMenu")}
        className={`pv-header-user-trigger ${open || accountActive ? "pv-header-user-trigger-active" : ""}`}
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
                    onClose();
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
            <button type="button" onClick={onLogout} className="pv-header-menu-link w-full">
              {t("nav.logout")}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
