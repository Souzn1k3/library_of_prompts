"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { trackEvent } from "@/lib/analytics";
import { ApiRequestError } from "@/lib/api";
import { fetchMissions } from "@/lib/client-api";
import { getMissionStatusTranslationKey } from "@/lib/i18n";
import type { MissionListRead, MissionRead } from "@/lib/types";

export function MissionsClient() {
  const { t, language } = useI18n();
  const [data, setData] = useState<MissionListRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetchMissions()
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((e) => {
        setData(null);
        if (e instanceof ApiRequestError && e.status === 401) {
          setError("signed_out");
        } else {
          setError(e instanceof Error ? e.message : t("missions.loadFailed"));
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [language, reloadToken, t]);

  if (error === "signed_out") {
    return (
      <p className="text-sm text-zinc-600">
        {t("missions.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("missions.signInLink")}
        </Link>{" "}
        {t("missions.signInSuffix")}
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

  if (loading || !data) {
    return <p className="text-sm text-zinc-500">{t("missions.loading")}</p>;
  }

  if (data.missions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-6 text-sm text-zinc-600">
        {t("missions.empty")}
      </div>
    );
  }

  const percent = data.total_count > 0 ? Math.round((data.completed_count / data.total_count) * 100) : 0;

  return (
    <div className="space-y-5">
      <section className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
        <p className="text-sm text-zinc-700">
          {t("missions.completedSummary")}: <span className="font-medium text-zinc-900">{data.completed_count}</span> /{" "}
          {data.total_count}
        </p>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-zinc-200">
          <div className="h-full rounded-full bg-zinc-900" style={{ width: `${percent}%` }} />
        </div>
        <p className="mt-2 text-xs text-zinc-500">
          {t("missions.missionCredits")}: <span className="font-medium text-zinc-700">{data.rewards.credits}</span>
          {data.rewards.badges.length ? (
            <>
              {" "}
              · {t("missions.badges")}: <span className="font-medium text-zinc-700">{data.rewards.badges.join(", ")}</span>
            </>
          ) : null}
        </p>
      </section>

      <div className="space-y-3">
        {data.missions.map((mission) => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
      </div>
    </div>
  );
}

function MissionCard({ mission }: { mission: MissionRead }) {
  const { t } = useI18n();
  const pct = Math.round((mission.progress_count / Math.max(1, mission.required_count)) * 100);

  function trackNextStep() {
    if (!mission.next_step) return;
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: "/missions",
      feature: "mission_loop",
      metadata: {
        mission_id: mission.id,
        mission_slug: mission.slug,
        status: mission.status,
        progress_count: mission.progress_count,
        required_count: mission.required_count,
        action: mission.next_step.action,
        href: mission.next_step.href,
      },
    });
  }

  return (
    <article className="space-y-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-zinc-900">{mission.title}</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            mission.status === "completed"
              ? "bg-emerald-100 text-emerald-900"
              : mission.status === "in_progress"
                ? "bg-blue-100 text-blue-900"
                : "bg-zinc-100 text-zinc-700"
          }`}
        >
          {t(getMissionStatusTranslationKey(mission.status))}
        </span>
      </div>
      {mission.description ? <p className="text-sm text-zinc-600">{mission.description}</p> : null}
      <p className="text-sm text-zinc-800">
        <span className="font-medium">{t("missions.objective")}:</span> {mission.objective}
      </p>
      <p className="text-xs text-zinc-500">
        {t("missions.completion")}: {mission.completion_condition}
      </p>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
        <div className="h-full rounded-full bg-zinc-900" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-zinc-500">
        {t("missions.progress")}: {mission.progress_count}/{mission.required_count}
      </p>
      <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
        {mission.reward.badge ? <span>{t("missions.badge")}: {mission.reward.badge}</span> : null}
        {mission.reward.credits ? <span>{t("missions.credits")}: +{mission.reward.credits}</span> : null}
        {mission.reward.premium_days ? (
          <span>
            {t("missions.premiumUnlockDays")}: {mission.reward.premium_days}
          </span>
        ) : null}
      </div>
      {mission.prompts.length ? (
        <p className="text-xs text-zinc-500">
          {t("missions.linkedPrompts")}: {mission.prompts.map((prompt) => prompt.title).join(", ")}
        </p>
      ) : null}
      {mission.lesson ? (
        <p className="text-xs text-zinc-500">
          {t("missions.linkedLesson")}: {mission.lesson.title}
          {mission.lesson.locked ? ` (${t("missionDetail.locked")})` : ""}
        </p>
      ) : null}
      {mission.next_step ? (
        <Link
          href={mission.next_step.href}
          onClick={trackNextStep}
          className="inline-flex items-center rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-800"
        >
          {mission.next_step.label}
        </Link>
      ) : null}
      {mission.completed_at ? (
        <p className="text-xs text-emerald-700">
          {t("missions.completedAt")}: {new Date(mission.completed_at).toLocaleString()}
        </p>
      ) : null}
    </article>
  );
}
