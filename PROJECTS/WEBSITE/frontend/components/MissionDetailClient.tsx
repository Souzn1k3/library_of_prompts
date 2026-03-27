"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { fetchMissionBySlug } from "@/lib/client-api";
import type { MissionRead } from "@/lib/types";

export function MissionDetailClient({ slug }: { slug: string }) {
  const { t, language } = useI18n();
  const [mission, setMission] = useState<MissionRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetchMissionBySlug(slug)
      .then((row) => {
        setMission(row);
        setError(null);
      })
      .catch((e) => {
        setMission(null);
        if (e instanceof ApiRequestError && e.status === 401) {
          setError("signed_out");
        } else {
          setError(e instanceof Error ? e.message : t("missionDetail.loadFailed"));
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug, language, reloadToken, t]);

  if (error === "signed_out") {
    return (
      <p className="text-sm text-zinc-600">
        {t("missionDetail.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("missionDetail.signInLink")}
        </Link>{" "}
        {t("missionDetail.signInSuffix")}
      </p>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (loading || !mission) {
    return <p className="text-sm text-zinc-500">{t("missionDetail.loading")}</p>;
  }

  const currentMission = mission;
  const pct = Math.round((currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100);
  const nextStep =
    currentMission.next_step?.href === `/missions/${currentMission.slug}` ? null : currentMission.next_step;

  function trackNextStep() {
    if (!nextStep) return;
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: `/missions/${currentMission.slug}`,
      feature: "mission_detail",
      metadata: {
        mission_id: currentMission.id,
        mission_slug: currentMission.slug,
        status: currentMission.status,
        progress_count: currentMission.progress_count,
        required_count: currentMission.required_count,
        action: nextStep.action,
        href: nextStep.href,
      },
    });
  }

  return (
    <article className="space-y-4 rounded-lg border border-zinc-200 bg-white p-5 shadow-card">
      <h1 className="text-2xl font-semibold text-zinc-900">{currentMission.title}</h1>
      {currentMission.description ? <p className="text-sm text-zinc-600">{currentMission.description}</p> : null}
      <p className="text-sm text-zinc-800">
        <span className="font-medium">{t("missionDetail.objective")}:</span> {currentMission.objective}
      </p>
      <p className="text-sm text-zinc-600">
        {t("missionDetail.completionCondition")}: {currentMission.completion_condition}
      </p>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
        <div className="h-full rounded-full bg-zinc-900" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-zinc-500">
        {t("missionDetail.progress")}: {currentMission.progress_count}/{currentMission.required_count}
      </p>
      {nextStep ? (
        <Link
          href={nextStep.href}
          onClick={trackNextStep}
          className="inline-flex items-center rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-800"
        >
          {nextStep.label}
        </Link>
      ) : null}
      {currentMission.prompts.length ? (
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            {t("missionDetail.linkedPrompts")}
          </p>
          <ul className="space-y-1 text-sm text-zinc-700">
            {currentMission.prompts.map((prompt) => (
              <li key={prompt.id}>
                <Link href={`/prompt/${prompt.slug}`} className="underline">
                  {prompt.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {currentMission.lesson ? (
        <p className="text-sm text-zinc-700">
          {t("missionDetail.linkedLesson")}:{" "}
          <Link href={`/learn/${currentMission.lesson.slug}`} className="underline">
            {currentMission.lesson.title}
          </Link>
          {currentMission.lesson.locked ? ` (${t("missionDetail.locked")})` : ""}
        </p>
      ) : null}
      <p className="text-xs text-zinc-500">
        {t("missionDetail.reward")}:{" "}
        {currentMission.reward.badge
          ? `${t("missions.badge")} ${currentMission.reward.badge}`
          : t("missionDetail.noBadge")}
        {currentMission.reward.credits ? ` · +${currentMission.reward.credits} ${t("missionDetail.credits")}` : ""}
        {currentMission.reward.premium_days
          ? ` · ${currentMission.reward.premium_days} ${t("missionDetail.premiumUnlockDays")}`
          : ""}
      </p>
    </article>
  );
}
