"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PromptCard } from "@/components/PromptCard";
import { completeLesson, fetchPromptRecommendations } from "@/lib/client-api";
import type { PromptListItem } from "@/lib/types";

export function CompleteLessonButton({ slug }: { slug: string }) {
  const { status } = useAuth();
  const { t } = useI18n();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<PromptListItem[]>([]);

  async function markCompleted() {
    setPending(true);
    setError(null);
    try {
      await completeLesson(slug);
      setDone(true);
      try {
        const response = await fetchPromptRecommendations({
          context: "after_lesson_complete",
          limit: 3,
          lesson_slug: slug,
        });
        setRecommendations(response.items);
      } catch {
        setRecommendations([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("api.requestFailed"));
    } finally {
      setPending(false);
    }
  }

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <p className="text-sm text-zinc-600">
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("nav.login")}
        </Link>{" "}
        {t("learn.trackAuthSuffix")}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {!done ? (
        <button
          type="button"
          onClick={markCompleted}
          disabled={pending}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-60"
        >
          {pending ? t("learn.completeUpdating") : t("learn.markComplete")}
        </button>
      ) : (
        <div className="space-y-3">
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            {t("learn.completeTracked")}{" "}
            <Link href="/missions" className="font-medium underline">
              {t("learn.continueMission")}
            </Link>
            .
          </div>
          {recommendations.length > 0 ? (
            <section className="space-y-3 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
              <p className="text-sm font-medium text-zinc-900">{t("learn.nextPromptsTitle")}</p>
              <p className="text-sm text-zinc-600">{t("learn.nextPromptsBody")}</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {recommendations.map((prompt) => (
                  <PromptCard key={`after-lesson-${prompt.id}`} prompt={prompt} />
                ))}
              </div>
            </section>
          ) : null}
        </div>
      )}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
