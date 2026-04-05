"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useCallback } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { SubmitPromptAdvancedFields } from "@/components/submit/SubmitPromptAdvancedFields";
import { SubmitPromptBasicFields } from "@/components/submit/SubmitPromptBasicFields";
import { useSubmitPromptForm } from "@/components/submit/useSubmitPromptForm";
import { APP_ROUTES } from "@/lib/constants/routes";

export function SubmitPromptForm() {
  const router = useRouter();
  const { status } = useAuth();
  const { t, language } = useI18n();

  const handleSubmitted = useCallback(
    (result: { auto_approved?: boolean }) => {
      const searchParams = new URLSearchParams();
      searchParams.set("submitted", "1");
      if (result.auto_approved) {
        searchParams.set("autoApproved", "1");
      }
      router.push(`${APP_ROUTES.dashboard}?${searchParams.toString()}`);
    },
    [router],
  );

  const {
    categories,
    discoveryFilters,
    pending,
    error,
    bootstrapLoading,
    bootstrapError,
    reloadOptions,
    submitFromForm,
  } = useSubmitPromptForm({
    language,
    t,
    onSubmitted: handleSubmitted,
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitFromForm(event.currentTarget);
  }

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{t("submit.authRequired")}</p>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link href={APP_ROUTES.login} className="font-medium text-amber-950 underline">
            {t("nav.login")}
          </Link>
          <Link href={APP_ROUTES.signup} className="font-medium text-amber-950 underline">
            {t("nav.signup")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit}>
      {error ? (
        <div className="rounded-[1rem] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {bootstrapError ? (
        <div className="space-y-2 rounded-[1rem] border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <p>{bootstrapError}</p>
          <button
            type="button"
            onClick={reloadOptions}
            className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
          >
            {t("submit.retryLoadingOptions")}
          </button>
        </div>
      ) : null}

      <SubmitPromptBasicFields
        categories={categories}
        bootstrapLoading={bootstrapLoading}
        t={t}
      />
      <SubmitPromptAdvancedFields discoveryFilters={discoveryFilters} t={t} />

      <div className="pv-form-card">
        <div className="pv-field">
          <label className="pv-label" htmlFor="body">
            {t("submit.bodyLabel")}
          </label>
          <textarea id="body" name="body" required rows={12} className="pv-textarea font-mono" />
        </div>
      </div>

      <button
        type="submit"
        disabled={pending || bootstrapLoading || categories.length === 0}
        className="pv-button-primary w-full disabled:opacity-60"
      >
        {bootstrapLoading ? t("submit.loadingForm") : pending ? t("submit.submitPending") : t("submit.submitIdle")}
      </button>
    </form>
  );
}

