"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getToken, setToken } from "@/lib/auth";

export function HeaderNav() {
  const [authed, setAuthed] = useState(false);

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
          Dashboard
        </Link>
        <button
          type="button"
          onClick={logout}
          className="text-sm text-zinc-600 transition hover:text-zinc-900"
        >
          Log out
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
        Log in
      </Link>
      <Link
        href="/signup"
        className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-zinc-800"
      >
        Sign up
      </Link>
    </>
  );
}
