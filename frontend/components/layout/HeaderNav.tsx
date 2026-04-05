"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  HeaderNavAuthenticatedDesktop,
  HeaderNavAuthenticatedMobile,
} from "@/components/layout/HeaderNavAuthenticated";
import { getInitials } from "@/components/layout/headerNavUtils";
import { getAccountMenuItems, isAccountMenuItemActive } from "@/lib/navigation";

type HeaderNavProps = {
  mobile?: boolean;
  onNavigate?: () => void;
};

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
        <HeaderNavAuthenticatedMobile
          userLabel={userLabel}
          userInitials={userInitials}
          pathname={pathname}
          menuItems={menuItems}
          onNavigate={onNavigate}
          onLogout={handleLogout}
          t={t}
        />
      );
    }

    return (
      <HeaderNavAuthenticatedDesktop
        menuRef={menuRef}
        userLabel={userLabel}
        userInitials={userInitials}
        pathname={pathname}
        menuItems={menuItems}
        open={open}
        accountActive={accountActive}
        onToggle={() => setOpen((value) => !value)}
        onNavigate={onNavigate}
        onClose={() => setOpen(false)}
        onLogout={handleLogout}
        t={t}
      />
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
