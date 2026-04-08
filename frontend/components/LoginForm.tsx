"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
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
      await loginRequest(email, password);
      await refreshAuth().catch(() => null);
      try {
        const onboarding = await fetchOnboardingProfile();
        router.replace(onboarding.needs_onboarding ? "/onboarding" : "/dashboard");
      } catch {
        router.replace("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("login.failed"));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {error ? (
        <div className="pv-alert pv-alert-error text-sm">
          {error}
        </div>
      ) : null}
      <div className="pv-field">
        <label htmlFor="email" className="pv-label">
          {t("login.emailLabel")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="pv-input"
          placeholder={t("login.emailPlaceholder")}
        />
      </div>
      <div className="pv-field">
        <label htmlFor="password" className="pv-label">
          {t("login.passwordLabel")}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
          minLength={8}
          className="pv-input"
          placeholder={t("login.passwordPlaceholder")}
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="pv-button-primary w-full disabled:opacity-60"
      >
        {pending ? t("login.submitPending") : t("login.submitIdle")}
      </button>
      <p className="text-center text-sm text-zinc-600">
        {t("login.noAccountPrefix")}{" "}
        <Link href="/signup" className="pv-inline-link">
          {t("login.noAccountLink")}
        </Link>
      </p>
    </form>
  );
}
