"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { TelegramAuthButton } from "@/components/TelegramAuthButton";
import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { fetchOnboardingProfile, registerRequest } from "@/lib/client-api";

export function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshAuth } = useAuth();
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const telegramErrorCode = searchParams.get("telegram_error");
  const telegramErrorKey =
    telegramErrorCode === "cancelled"
      ? "signup.telegramCancelled"
      : telegramErrorCode === "conflict"
        ? "signup.telegramConflict"
        : telegramErrorCode === "expired"
          ? "signup.telegramExpired"
          : telegramErrorCode === "not_configured"
            ? "signup.telegramUnavailable"
            : telegramErrorCode
              ? "signup.telegramFailed"
              : null;
  const visibleError = error ?? (telegramErrorKey ? t(telegramErrorKey) : null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const fd = new FormData(e.currentTarget);
    const email = String(fd.get("email") ?? "");
    const password = String(fd.get("password") ?? "");
    const displayName = String(fd.get("name") ?? "");
    try {
      await registerRequest(email, password, displayName);
      await refreshAuth().catch(() => null);
      try {
        const onboarding = await fetchOnboardingProfile();
        router.replace(onboarding.needs_onboarding ? "/onboarding" : "/dashboard");
      } catch {
        router.replace("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("signup.failed"));
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
        <label htmlFor="name" className="pv-label">
          {t("signup.nameLabel")}
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          minLength={1}
          maxLength={120}
          className="pv-input"
          placeholder={t("signup.namePlaceholder")}
        />
      </div>
      <div className="pv-field">
        <label htmlFor="email" className="pv-label">
          {t("signup.emailLabel")}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="pv-input"
          placeholder={t("signup.emailPlaceholder")}
        />
      </div>
      <div className="pv-field">
        <label htmlFor="password" className="pv-label">
          {t("signup.passwordLabel")}
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          className="pv-input"
          placeholder={t("signup.passwordPlaceholder")}
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="pv-button-primary w-full disabled:opacity-60"
      >
        {pending ? t("signup.submitPending") : t("signup.submitIdle")}
      </button>

      <div className="space-y-3 rounded-[1.1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] p-4">
        <p className="text-sm font-medium text-zinc-900">{t("signup.telegramTitle")}</p>
        <p className="text-sm text-zinc-600">{t("signup.telegramBody")}</p>
        <TelegramAuthButton
          label={t("signup.telegramAction")}
          mode="login"
          nextPath="/dashboard"
          className="w-full justify-center"
        />
      </div>

      <div className="border-t border-[var(--pv-border)] pt-4">
        <p className="text-center text-sm text-zinc-600">
          {t("signup.haveAccountPrefix")}{" "}
          <Link href="/login" className="font-medium text-[var(--pv-brand-strong)]">
            {t("signup.haveAccountLink")}
          </Link>
        </p>
      </div>
    </form>
  );
}
