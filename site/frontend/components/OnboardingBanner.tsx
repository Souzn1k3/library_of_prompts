"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const STORAGE_KEY = "pv_onboarding_dismissed_v1";

export function OnboardingBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      setVisible(!window.localStorage.getItem(STORAGE_KEY));
    } catch {
      setVisible(true);
    }
  }, []);

  function dismiss() {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
    setVisible(false);
  }

  if (!visible) {
    return null;
  }

  return (
    <div className="border-b border-zinc-200 bg-zinc-50">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-3 text-sm text-zinc-800 sm:flex-row sm:items-center sm:justify-between">
        <p className="leading-relaxed">
          <span className="font-medium text-zinc-900">Welcome.</span> Browse the{" "}
          <Link href="/catalog" className="underline">
            catalog
          </Link>
          , learn{" "}
          <Link href="/learn" className="underline">
            prompt patterns
          </Link>
          , or{" "}
          <Link href="/signup" className="underline">
            create an account
          </Link>{" "}
          to save prompts and submit your own.
        </p>
        <button
          type="button"
          onClick={dismiss}
          className="shrink-0 rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-900 transition hover:border-zinc-400"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
