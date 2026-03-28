"use client";

import { useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { trackPromptCopy } from "@/lib/client-api";

export function CopyPromptButton({
  promptId,
  body,
  metadata,
}: {
  promptId: string;
  body: string;
  metadata?: Record<string, unknown>;
}) {
  const { t } = useI18n();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

      try {
        await trackPromptCopy(promptId);
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
    </div>
  );
}
