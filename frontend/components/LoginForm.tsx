"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { TelegramAuthButton } from "@/components/TelegramAuthButton";
import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { fetchOnboardingProfile, loginRequest } from "@/lib/client-api";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshAuth } = useAuth();
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const telegramErrorCode = searchParams.get("telegram_error");
  const telegramErrorKey =
    telegramErrorCode === "cancelled"
      ? "login.telegramCancelled"
      : telegramErrorCode === "conflict"
        ? "login.telegramConflict"
        : telegramErrorCode === "expired"
          ? "login.telegramExpired"
          : telegramErrorCode === "not_configured"
            ? "login.telegramUnavailable"
            : telegramErrorCode
              ? "login.telegramFailed"
              : null;
  const visibleError = error ?? (telegramErrorKey ? t(telegramErrorKey) : null);

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
    <form className="space-y-5" onSubmit={onSubmit}>
      {visibleError ? (
        <div className="pv-alert pv-alert-error text-sm">
          {visibleError}
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

      <div className="space-y-3 rounded-[1.1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] p-4">
        <p className="text-sm font-medium text-zinc-900">{t("login.telegramTitle")}</p>
        <p className="text-sm text-zinc-600">{t("login.telegramBody")}</p>
        <TelegramAuthButton
          label={t("login.telegramAction")}
          mode="login"
          nextPath="/dashboard"
          className="w-full justify-center"
        />
      </div>

      <div className="border-t border-[var(--pv-border)] pt-4">
        <p className="text-center text-sm text-zinc-600">
          {t("login.noAccountPrefix")}{" "}
          <Link href="/signup" className="font-medium text-[var(--pv-brand-strong)]">
            {t("login.noAccountLink")}
          </Link>
        </p>
      </div>
    </form>
  );
}
