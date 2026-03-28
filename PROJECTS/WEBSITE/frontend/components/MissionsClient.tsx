"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { trackEvent } from "@/lib/analytics";
import { ApiRequestError } from "@/lib/api";
import { fetchMissions } from "@/lib/client-api";
import { getMissionStatusTranslationKey, type TranslationKey } from "@/lib/i18n";
import type { MissionListRead, MissionRead, MissionType } from "@/lib/types";

const SECTION_ORDER: MissionType[] = ["progression", "learning", "action", "streak", "challenge"];

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

  const currentMission = useMemo(() => {
    if (!data?.current_mission_slug) return data?.missions.find((mission) => mission.status === "in_progress") ?? null;
    return data.missions.find((mission) => mission.slug === data.current_mission_slug) ?? null;
  }, [data]);

  const sections = useMemo(() => {
    if (!data) return [];
    return SECTION_ORDER.map((type) => ({
      type,
      items: data.missions.filter((mission) => mission.mission_type === type),
    })).filter((section) => section.items.length > 0);
  }, [data]);

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
      <div className="space-y-3 rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-900 transition hover:border-amber-400"
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
      <div className="rounded-[1.25rem] border border-dashed border-zinc-300 bg-zinc-50/80 p-6 text-sm text-zinc-600">
        {t("missions.empty")}
      </div>
    );
  }

  const percent = data.total_count > 0 ? Math.round((data.completed_count / data.total_count) * 100) : 0;

  return (
    <div className="space-y-6">
      <section className="pv-panel px-5 py-5 sm:px-6">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
          <div className="space-y-4">
            <div>
              <p className="pv-kicker">{t("missions.completedSummary")}</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-zinc-950">
                {currentMission ? currentMission.title : t("missions.title")}
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-zinc-600">
                {currentMission?.objective ?? t("missions.subtitle")}
              </p>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
              <div className="h-full rounded-full bg-[var(--pv-brand)]" style={{ width: `${percent}%` }} />
            </div>

            <div className="flex flex-wrap gap-4 text-sm text-zinc-600">
              <span>
                {data.completed_count} / {data.total_count}
              </span>
              <span>
                {data.rewards.credits} {t("missions.credits")}
              </span>
              <span>
                {data.rewards.badges.length} {t("missions.badges")}
              </span>
            </div>

            <div className="flex flex-wrap gap-3">
              {currentMission?.next_step ? (
                <Link href={currentMission.next_step.href} className="pv-button-primary">
                  {currentMission.next_step.label}
                </Link>
              ) : (
                <Link href="/catalog" className="pv-button-primary">
                  {t("home.explorePrompts")}
                </Link>
              )}
              <Link href="/wallet" className="pv-button-secondary">
                {t("nav.wallet")}
              </Link>
              <Link href="/store" className="pv-button-secondary">
                {t("nav.store")}
              </Link>
            </div>
          </div>

          <div className="rounded-[1.25rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              {currentMission ? t("missions.progress") : t("missions.title")}
            </p>
            {currentMission ? (
              <div className="mt-3 space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-zinc-700">
                    {t(`missions.type.${currentMission.mission_type}` as TranslationKey)}
                  </span>
                  <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-zinc-700">
                    {t(getMissionStatusTranslationKey(currentMission.status))}
                  </span>
                  {currentMission.is_repeatable ? (
                    <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-zinc-700">
                      {t("missions.repeatable")}
                    </span>
                  ) : null}
                </div>
                <p className="text-sm text-zinc-700">
                  {t("missions.progress")}: {currentMission.progress_count}/{currentMission.required_count}
                </p>
                {currentMission.completion_count > 0 ? (
                  <p className="text-sm text-zinc-600">
                    {t("missions.completedTimes")}: {currentMission.completion_count}
                  </p>
                ) : null}
                {currentMission.available_again_at ? (
                  <p className="text-sm text-zinc-600">
                    {t("missions.availableAgain")}: {new Date(currentMission.available_again_at).toLocaleString()}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="mt-3 text-sm text-zinc-600">{t("missions.empty")}</p>
            )}
          </div>
        </div>
      </section>

      {sections.map((section) => (
        <section key={section.type} className="space-y-3">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t(`missions.type.${section.type}` as TranslationKey)}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {t(`missions.type.${section.type}` as TranslationKey)}
              </h2>
            </div>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            {section.items.map((mission) => (
              <MissionCard key={mission.id} mission={mission} />
            ))}
          </div>
        </section>
      ))}
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
    <article className="pv-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
              {t(`missions.type.${mission.mission_type}` as TranslationKey)}
            </span>
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                mission.status === "completed"
                  ? "bg-emerald-100 text-emerald-900"
                  : mission.status === "in_progress"
                    ? "bg-blue-100 text-blue-900"
                    : "bg-zinc-100 text-zinc-700"
              }`}
            >
              {t(getMissionStatusTranslationKey(mission.status))}
            </span>
            {mission.is_repeatable ? (
              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                {t("missions.repeatable")}
              </span>
            ) : null}
          </div>
          <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{mission.title}</h3>
          <p className="text-sm text-zinc-600">{mission.objective}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {mission.next_step ? (
            <Link href={mission.next_step.href} onClick={trackNextStep} className="pv-button-primary">
              {mission.next_step.label}
            </Link>
          ) : null}
          <Link href={`/missions/${mission.slug}`} className="pv-button-secondary">
            {t("dashboard.openMissionDetails")}
          </Link>
        </div>
      </div>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-200">
        <div className="h-full rounded-full bg-[var(--pv-brand)]" style={{ width: `${pct}%` }} />
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-zinc-500">
        <span>
          {t("missions.progress")}: {mission.progress_count}/{mission.required_count}
        </span>
        {mission.reward.credits > 0 ? (
          <span>
            {t("missions.credits")}: +{mission.reward.credits}
          </span>
        ) : null}
        {mission.reward.badge ? (
          <span>
            {t("missions.badge")}: {mission.reward.badge}
          </span>
        ) : null}
        {mission.completion_count > 0 ? (
          <span>
            {t("missions.completedTimes")}: {mission.completion_count}
          </span>
        ) : null}
      </div>

      {mission.available_again_at ? (
        <p className="mt-3 text-xs text-zinc-500">
          {t("missions.availableAgain")}: {new Date(mission.available_again_at).toLocaleString()}
        </p>
      ) : null}
    </article>
  );
}
