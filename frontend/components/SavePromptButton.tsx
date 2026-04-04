"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PromptCard } from "@/components/PromptCard";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { fetchPromptRecommendations, fetchSavedPrompts, savePrompt, unsavePrompt } from "@/lib/client-api";
import type { EconomyAction, PromptListItem } from "@/lib/types";

export function SavePromptButton({
  promptId,
  promptSlug,
  metadata,
}: {
  promptId: string;
  promptSlug?: string;
  metadata?: Record<string, unknown>;
}) {
  const { t } = useI18n();
  const { status } = useAuth();
  const [saved, setSaved] = useState(false);
  const [recommendations, setRecommendations] = useState<PromptListItem[]>([]);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [savedLoading, setSavedLoading] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    if (status !== "authenticated") {
      setSaved(false);
      setRecommendations([]);
      setSavedLoading(false);
      return;
    }

    let cancelled = false;
    setSavedLoading(true);
    fetchSavedPrompts()
      .then((list) => {
        if (cancelled) {
          return;
        }
        setSaved(list.some((p) => p.id === promptId));
      })
      .catch((e) => {
        if (cancelled || (e instanceof ApiRequestError && e.status === 401)) {
          return;
        }
        setError(e instanceof ApiRequestError ? e.message : t("save.updateFailed"));
      })
      .finally(() => {
        if (!cancelled) {
          setSavedLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [promptId, status, t]);

  async function toggle() {
    if (status !== "authenticated") {
      return;
    }
    setError(null);
    setPending(true);
    try {
      if (saved) {
        await unsavePrompt(promptId);
        setSaved(false);
        setRecommendations([]);
        setEconomy(null);
      } else {
        const action = await savePrompt(promptId);
        setSaved(true);
        setEconomy(action);
        if (promptSlug) {
          try {
            const response = await fetchPromptRecommendations({
              context: "after_save",
              limit: 3,
              prompt_slug: promptSlug,
            });
            setRecommendations(response.items);
          } catch {
            setRecommendations([]);
          }
        }
        const page = typeof window !== "undefined" ? window.location.pathname : "/prompt";
        const baseMeta = {
          prompt_id: promptId,
          ...(metadata ?? {}),
        };
        trackEvent({
          eventName: "prompt_saved",
          page,
          feature: "prompt_save",
          metadata: baseMeta,
        });
        trackEvent({
          eventName: "submission_engaged",
          page,
          feature: "contributor_engagement",
          metadata: baseMeta,
        });
      }
    } catch (e) {
      if (e instanceof ApiRequestError && e.status === 409) {
        setSaved(true);
      } else {
        setError(e instanceof ApiRequestError ? e.message : t("save.updateFailed"));
      }
    } finally {
      setPending(false);
    }
  }

  if (status === "unauthenticated") {
    return (
      <p className="text-sm text-zinc-500">
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("save.loginLink")}
        </Link>{" "}
        {t("save.loginSuffix")}
      </p>
    );
  }

  if (status === "loading" || savedLoading) {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={toggle}
        disabled={pending}
        className="pv-button-secondary !w-auto whitespace-nowrap disabled:opacity-60"
      >
        {pending ? t("save.pending") : saved ? t("save.savedRemove") : t("save.saveToDashboard")}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <EconomyActionBanner summary={economy} />
      {recommendations.length > 0 ? (
        <section className="pv-card space-y-3 p-4">
          <p className="text-sm font-medium text-zinc-900">{t("save.keepMomentum")}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {recommendations.map((prompt) => (
              <PromptCard key={`after-save-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
