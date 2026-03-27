"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { fetchOnboardingProfile, loginRequest } from "@/lib/client-api";

export function LoginForm() {
  const router = useRouter();
  const { refreshAuth } = useAuth();
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const fd = new FormData(e.currentTarget);
    const email = String(fd.get("email") ?? "");
    const password = String(fd.get("password") ?? "");
    try {
      const token = await loginRequest(email, password);
      setToken(token.access_token);
      await refreshAuth().catch(() => null);
      try {
        const onboarding = await fetchOnboardingProfile();
        router.push(onboarding.needs_onboarding ? "/onboarding" : "/dashboard");
      } catch {
        router.push("/dashboard");
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("login.failed"));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}
      <div className="space-y-1">
        <label htmlFor="email" className="text-xs font-medium text-zinc-700">
          {t("login.emailLabel")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          placeholder={t("login.emailPlaceholder")}
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="password" className="text-xs font-medium text-zinc-700">
          {t("login.passwordLabel")}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          minLength={8}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          placeholder={t("login.passwordPlaceholder")}
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-60"
      >
        {pending ? t("login.submitPending") : t("login.submitIdle")}
      </button>
      <p className="text-center text-sm text-zinc-600">
        {t("login.noAccountPrefix")}{" "}
        <Link href="/signup" className="font-medium text-zinc-900 underline">
          {t("login.noAccountLink")}
        </Link>
      </p>
    </form>
  );
}
