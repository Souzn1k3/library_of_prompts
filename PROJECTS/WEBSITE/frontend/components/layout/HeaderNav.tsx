"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getToken, setToken } from "@/lib/auth";

export function HeaderNav() {
  const [authed, setAuthed] = useState(false);
  const { t } = useI18n();

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  function logout() {
    setToken(null);
    setAuthed(false);
    window.location.href = "/";
  }

  if (authed) {
    return (
      <>
        <Link href="/dashboard" className="transition hover:text-zinc-900">
          {t("nav.dashboard")}
        </Link>
        <button
          type="button"
          onClick={logout}
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
