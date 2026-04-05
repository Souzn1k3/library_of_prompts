"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { fetchPromptRecommendations, fetchSavedPrompts, savePrompt, unsavePrompt } from "@/lib/client-api";
import { getDifficultyTranslationKey, getTechniqueTranslationKey } from "@/lib/i18n";
import type { EconomyAction, PromptListItem } from "@/lib/types";

const AFTER_SAVE_RECOMMENDATION_LIMIT = 2;
const AFTER_SAVE_FETCH_LIMIT = 8;
const RECOMMENDATION_REASON_KEYS = [
  "recommendation.reason.related",
  "recommendation.reason.behavior",
  "recommendation.reason.lesson",
  "recommendation.reason.level",
  "recommendation.reason.trending",
  "recommendation.reason.curated",
  "recommendation.reason.explore",
] as const;

type RecommendationReasonKey = (typeof RECOMMENDATION_REASON_KEYS)[number];

const RECOMMENDATION_REASON_PRIORITY: Record<RecommendationReasonKey, number> = {
  "recommendation.reason.related": 0,
  "recommendation.reason.behavior": 1,
  "recommendation.reason.lesson": 2,
  "recommendation.reason.level": 3,
  "recommendation.reason.trending": 4,
  "recommendation.reason.curated": 5,
  "recommendation.reason.explore": 6,
};

function isRecommendationReasonKey(value: string | null | undefined): value is RecommendationReasonKey {
  return typeof value === "string" && RECOMMENDATION_REASON_KEYS.some((key) => key === value);
}

function recommendationPriority(item: PromptListItem): number {
  if (!isRecommendationReasonKey(item.recommendation_reason_key)) {
    return 999;
  }
  return RECOMMENDATION_REASON_PRIORITY[item.recommendation_reason_key];
}

function selectAfterSaveRecommendations(
  items: PromptListItem[],
  promptSlug: string | undefined,
  limit: number,
): PromptListItem[] {
  const seenIds = new Set<string>();
  const filtered: PromptListItem[] = [];
  for (const item of items) {
    if (!item?.id || seenIds.has(item.id)) {
      continue;
    }
    if (promptSlug && item.slug === promptSlug) {
      continue;
    }
    seenIds.add(item.id);
    filtered.push(item);
  }

  filtered.sort((a, b) => {
    const priorityDelta = recommendationPriority(a) - recommendationPriority(b);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }
    const qualityDelta = (b.quality_score ?? -1) - (a.quality_score ?? -1);
    if (qualityDelta !== 0) {
      return qualityDelta;
    }
    const savesDelta = (b.save_count ?? -1) - (a.save_count ?? -1);
    if (savesDelta !== 0) {
      return savesDelta;
    }
    return a.title.localeCompare(b.title);
  });

  const diverse: PromptListItem[] = [];
  const usedReasons = new Set<RecommendationReasonKey>();
  for (const item of filtered) {
    if (!isRecommendationReasonKey(item.recommendation_reason_key)) {
      continue;
    }
    if (usedReasons.has(item.recommendation_reason_key)) {
      continue;
    }
    diverse.push(item);
    usedReasons.add(item.recommendation_reason_key);
    if (diverse.length >= limit) {
      return diverse;
    }
  }

  for (const item of filtered) {
    if (diverse.some((picked) => picked.id === item.id)) {
      continue;
    }
    diverse.push(item);
    if (diverse.length >= limit) {
      break;
    }
  }
  return diverse.slice(0, limit);
}

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
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [savedLoading, setSavedLoading] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recommendationRequestSeq = useRef(0);

  useEffect(() => {
    setError(null);
    if (status !== "authenticated") {
      setSaved(false);
      setRecommendations([]);
      setRecommendationsLoading(false);
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
        recommendationRequestSeq.current += 1;
        await unsavePrompt(promptId);
        setSaved(false);
        setRecommendations([]);
        setRecommendationsLoading(false);
        setEconomy(null);
      } else {
        const action = await savePrompt(promptId);
        setSaved(true);
        setEconomy(action);
        setRecommendations([]);
        if (promptSlug) {
          const requestId = recommendationRequestSeq.current + 1;
          recommendationRequestSeq.current = requestId;
          setRecommendationsLoading(true);
          try {
            const response = await fetchPromptRecommendations({
              context: "after_save",
              limit: AFTER_SAVE_FETCH_LIMIT,
              prompt_slug: promptSlug,
            });
            if (recommendationRequestSeq.current === requestId) {
              setRecommendations(
                selectAfterSaveRecommendations(response.items, promptSlug, AFTER_SAVE_RECOMMENDATION_LIMIT),
              );
            }
          } catch {
            if (recommendationRequestSeq.current === requestId) {
              setRecommendations([]);
            }
          } finally {
            if (recommendationRequestSeq.current === requestId) {
              setRecommendationsLoading(false);
            }
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
      {saved && recommendationsLoading ? <p className="text-xs text-zinc-500">{t("common.loading")}</p> : null}
      {recommendations.length > 0 ? (
        <section className="rounded-[1rem] border border-[var(--pv-border)] bg-white/85 p-3 sm:p-4">
          <p className="text-sm font-medium text-zinc-900">{t("save.keepMomentum")}</p>
          <div className="mt-3 grid gap-2">
            {recommendations.map((prompt) => (
              <Link
                key={`after-save-${prompt.id}`}
                href={`/prompt/${encodeURIComponent(prompt.slug)}`}
                prefetch={false}
                className="group block rounded-[0.95rem] border border-[var(--pv-border)] bg-white/90 p-3 transition hover:border-[var(--pv-border-strong)] hover:shadow-[0_8px_20px_rgba(15,23,42,0.08)]"
              >
                <p className="line-clamp-1 text-[11px] font-semibold text-[var(--pv-brand-strong)]">
                  {isRecommendationReasonKey(prompt.recommendation_reason_key)
                    ? t(prompt.recommendation_reason_key)
                    : t("recommendation.reason.curated")}
                </p>
                <p className="mt-1 line-clamp-2 text-sm font-semibold leading-snug text-zinc-900">
                  {prompt.title}
                </p>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-zinc-600">
                  {prompt.summary ?? t("prompt.noSummary")}
                </p>

                <div className="mt-2 flex items-center justify-between gap-2 border-t border-[var(--pv-border)] pt-2">
                  <span className="line-clamp-1 text-[11px] text-zinc-500">
                    {prompt.difficulty
                      ? t(getDifficultyTranslationKey(prompt.difficulty))
                      : t(getTechniqueTranslationKey(prompt.technique))}
                  </span>
                  <span className="shrink-0 text-xs font-semibold text-[var(--pv-brand-strong)]">
                    {t("prompt.openPrompt")} ↗
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
