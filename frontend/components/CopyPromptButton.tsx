"use client";

import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { trackPromptCopy } from "@/lib/client-api";
import type { EconomyAction } from "@/lib/types";

type CopyPromptButtonVariant = "button" | "icon";

export function CopyPromptButton({
  promptId,
  body,
  metadata,
  variant = "button",
}: {
  promptId: string;
  body: string;
  metadata?: Record<string, unknown>;
  variant?: CopyPromptButtonVariant;
}) {
  const { t } = useI18n();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [animateSuccess, setAnimateSuccess] = useState(false);

  function toCopyErrorMessage(err: unknown): string {
    if (err instanceof DOMException && err.name === "NotAllowedError") {
      return t("copy.errorClipboardBlocked");
    }
    if (err instanceof ApiRequestError) {
      return err.message;
    }
    return t("copy.errorFailed");
  }

  async function copy() {
    setPending(true);
    setError(null);
    setDone(false);
    try {
      await navigator.clipboard.writeText(body);
      setDone(true);
      setAnimateSuccess(true);
      setEconomy(null);

      try {
        const action = await trackPromptCopy(promptId);
        setEconomy(action);
        trackEvent({
          eventName: "prompt_copied",
          page: typeof window !== "undefined" ? window.location.pathname : "/prompt",
          feature: "prompt_copy",
          metadata: {
            prompt_id: promptId,
            ...(metadata ?? {}),
          },
        });
      } catch (trackingError) {
        setError(
          trackingError instanceof ApiRequestError
            ? t("copy.analyticsFailed", { message: trackingError.message })
            : t("copy.analyticsFailedGeneric"),
        );
      }
    } catch (e) {
      setError(toCopyErrorMessage(e));
    } finally {
      setPending(false);
    }
  }

  useEffect(() => {
    if (!done) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setDone(false);
    }, 1500);
    return () => window.clearTimeout(timeoutId);
  }, [done]);

  useEffect(() => {
    if (!animateSuccess) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setAnimateSuccess(false);
    }, 260);
    return () => window.clearTimeout(timeoutId);
  }, [animateSuccess]);

  if (variant === "icon") {
    return (
      <div className="relative">
        <button
          type="button"
          onClick={copy}
          disabled={pending}
          className={`inline-flex h-8 w-8 items-center justify-center text-zinc-700 transition-transform duration-150 hover:scale-105 hover:text-zinc-900 disabled:cursor-not-allowed disabled:opacity-50 ${
            done ? "text-[#255cff]" : ""
          } ${animateSuccess ? "scale-110" : ""}`}
          aria-label={pending ? t("copy.copying") : done ? t("copy.copied") : t("copy.copyPrompt")}
          title={pending ? t("copy.copying") : done ? t("copy.copied") : t("copy.copyPrompt")}
        >
          {pending ? (
            <svg viewBox="0 0 24 24" className="h-6 w-6 animate-spin" aria-hidden="true" focusable="false">
              <circle cx="12" cy="12" r="7" fill="none" stroke="currentColor" strokeWidth="2.2" opacity="0.25" />
              <path d="M12 5a7 7 0 0 1 7 7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.1" aria-hidden="true" focusable="false">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75A2.25 2.25 0 0 1 11.25 10.5h4.5A2.25 2.25 0 0 1 18 12.75v4.5A2.25 2.25 0 0 1 15.75 19.5h-4.5A2.25 2.25 0 0 1 9 17.25v-4.5Z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 6.75A2.25 2.25 0 0 0 12.75 4.5h-4.5A2.25 2.25 0 0 0 6 6.75v4.5A2.25 2.25 0 0 0 8.25 13.5h4.5A2.25 2.25 0 0 0 15 11.25v-4.5Z"
              />
            </svg>
          )}
        </button>
        {error ? (
          <p className="absolute right-0 top-full z-10 mt-2 w-56 rounded-md border border-rose-200 bg-rose-50 px-2 py-1.5 text-[11px] leading-relaxed text-rose-700 shadow-sm">
            {error}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={copy}
        disabled={pending}
        className="pv-button-primary disabled:opacity-60"
      >
        {pending ? t("copy.copying") : done ? t("copy.copied") : t("copy.copyPrompt")}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <EconomyActionBanner summary={economy} />
    </div>
  );
}
