"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";

export function HeaderNav() {
  const router = useRouter();
  const { status, user, logout } = useAuth();
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
      <div className="flex flex-wrap items-center gap-2 text-sm">
        {user?.display_name ? (
          <span className="hidden rounded-full border border-[var(--pv-border)] bg-white/80 px-3 py-1.5 text-xs font-semibold text-zinc-700 lg:inline-flex">
            {user.display_name}
          </span>
        ) : null}
        <Link
          href="/dashboard"
          className="rounded-full border border-transparent px-3 py-1.5 font-medium text-zinc-700 transition hover:border-[var(--pv-border)] hover:bg-white hover:text-zinc-900"
        >
          {t("nav.dashboard")}
        </Link>
        <Link
          href="/profile"
          className="rounded-full border border-transparent px-3 py-1.5 font-medium text-zinc-700 transition hover:border-[var(--pv-border)] hover:bg-white hover:text-zinc-900"
        >
          {t("nav.profile")}
        </Link>
        <Link
          href="/store"
          className="rounded-full border border-transparent px-3 py-1.5 font-medium text-zinc-700 transition hover:border-[var(--pv-border)] hover:bg-white hover:text-zinc-900"
        >
          {t("nav.store")}
        </Link>
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-transparent px-3 py-1.5 font-medium text-zinc-700 transition hover:border-[var(--pv-border)] hover:bg-white hover:text-zinc-900"
        >
          {t("nav.logout")}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <Link
        href="/login"
        className="hidden rounded-full border border-transparent px-3 py-1.5 font-medium text-zinc-700 transition hover:border-[var(--pv-border)] hover:bg-white hover:text-zinc-900 sm:inline-flex"
      >
        {t("nav.login")}
      </Link>
      <Link
        href="/signup"
        className="rounded-full bg-[var(--pv-brand)] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[var(--pv-brand-strong)]"
      >
        {t("nav.signup")}
      </Link>
    </div>
  );
}
