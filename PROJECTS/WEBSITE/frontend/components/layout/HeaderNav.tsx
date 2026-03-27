"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function HeaderNav() {
  const router = useRouter();
  const { status, logout } = useAuth();
  const { t } = useI18n();

  async function handleLogout() {
    await logout();
    router.push("/");
    router.refresh();
  }

  if (status === "loading") {
    return <span className="hidden min-w-24 sm:inline-block" aria-hidden />;
  }

  if (status === "authenticated") {
    return (
      <>
        <Link href="/missions" className="transition hover:text-zinc-900">
          {t("nav.missions")}
        </Link>
        <Link href="/dashboard" className="transition hover:text-zinc-900">
          {t("nav.dashboard")}
        </Link>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-zinc-600 transition hover:text-zinc-900"
        >
          {t("nav.logout")}
        </button>
      </>
    );
  }

  return (
    <>
      <Link
        href="/login"
        className="hidden transition hover:text-zinc-900 sm:inline"
      >
        {t("nav.login")}
      </Link>
      <Link
        href="/signup"
        className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-800"
      >
        {t("nav.signup")}
      </Link>
    </>
  );
}
