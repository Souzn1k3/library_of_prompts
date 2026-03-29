"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
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
    if (!data?.current_mission_slug) {
      return data?.missions.find((mission) => mission.status === "in_progress") ?? null;
    }
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
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.missions")}
          title={t("missions.title")}
          description={t("missions.subtitle")}
          hint={t("economy.loopBody")}
          actions={
            <>
              <Link href="/login" className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href="/catalog" className="pv-inline-link">
                {t("home.explorePrompts")}
                <span aria-hidden="true">↗</span>
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("missions.signInPrefix")}{" "}
          <Link href="/login" className="font-medium text-zinc-900 underline">
            {t("missions.signInLink")}
          </Link>{" "}
          {t("missions.signInSuffix")}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.missions")}
          title={t("missions.title")}
          description={t("missions.subtitle")}
          hint={t("economy.loopBody")}
        />
        <div className="pv-alert pv-alert-warning space-y-3">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => setReloadToken((value) => value + 1)}
            className="pv-button-secondary !w-auto"
          >
            {t("dashboard.retry")}
          </button>
        </div>
      </div>
    );
  }

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.missions")}
          title={t("missions.title")}
          description={t("missions.subtitle")}
          hint={t("economy.loopBody")}
        />
        <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
      </div>
    );
  }

  if (data.missions.length === 0) {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.missions")}
          title={t("missions.title")}
          description={t("missions.subtitle")}
          hint={t("economy.loopBody")}
          actions={
            <>
              <Link href="/catalog" className="pv-button-primary">
                {t("home.explorePrompts")}
              </Link>
              <Link href="/dashboard" className="pv-button-secondary">
                {t("nav.dashboard")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">{t("missions.empty")}</div>
      </div>
    );
  }

  const percent = data.total_count > 0 ? Math.round((data.completed_count / data.total_count) * 100) : 0;
  const missionHint = currentMission?.next_step
    ? `${t("dashboard.recommendedNextAction")}: ${currentMission.next_step.label}`
    : t("economy.loopBody");

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow={t("nav.missions")}
        title={currentMission?.title ?? t("missions.title")}
        description={currentMission?.objective ?? t("missions.subtitle")}
        hint={missionHint}
        actions={
          <>
            {currentMission?.next_step ? (
              <Link href={currentMission.next_step.href} className="pv-button-primary">
                {currentMission.next_step.label}
              </Link>
            ) : (
              <Link href="/catalog" className="pv-button-primary">
                {t("home.explorePrompts")}
              </Link>
            )}
            <Link href="/dashboard" className="pv-button-secondary">
              {t("nav.dashboard")}
            </Link>
            <Link href="/wallet" className="pv-inline-link">
              {t("nav.wallet")}
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("missions.progress")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {data.completed_count}/{data.total_count}
              </p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("missions.credits")}</p>
              <div className="mt-3">
                <LmnAmount amount={data.rewards.credits} symbol="LMN" />
              </div>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("missions.badges")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {data.rewards.badges.length}
              </p>
            </div>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="pv-progress">
            <div className="pv-progress-fill" style={{ width: `${percent}%` }} />
          </div>
          {currentMission ? (
            <div className="pv-note flex flex-wrap items-center gap-2">
              <span className="pv-badge-brand">{t(`missions.type.${currentMission.mission_type}` as TranslationKey)}</span>
              <span className="pv-badge">{t(getMissionStatusTranslationKey(currentMission.status))}</span>
              {currentMission.is_repeatable ? <span className="pv-badge">{t("missions.repeatable")}</span> : null}
            </div>
          ) : null}
        </div>
      </PageIntro>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <EconomyLoop activeStep="missions" />
      </section>

      {sections.map((section) => (
        <section key={section.type} className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t(`missions.type.${section.type}` as TranslationKey)}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                {t(`missions.type.${section.type}` as TranslationKey)}
              </h2>
            </div>
            <span className="pv-chip-brand">{section.items.length}</span>
          </div>
          <div className="mt-6 grid gap-4 xl:grid-cols-2">
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
  const tone = getMissionTone(mission.mission_type);

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
      <div className={`pointer-events-none absolute right-4 top-4 h-20 w-20 rounded-full blur-2xl ${tone.glow}`} />
      <div className="relative flex h-full flex-col gap-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${tone.badge}`}>
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
              {mission.is_repeatable ? <span className="pv-badge">{t("missions.repeatable")}</span> : null}
            </div>
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{mission.title}</h3>
            <p className="text-sm leading-relaxed text-zinc-600">{mission.objective}</p>
          </div>

          {mission.reward.credits > 0 ? <LmnAmount amount={`+${mission.reward.credits}`} symbol="LMN" /> : null}
        </div>

        <div className="pv-progress">
          <div className="pv-progress-fill" style={{ width: `${pct}%` }} />
        </div>

        <div className="flex flex-wrap gap-3 text-xs text-zinc-500">
          <span>
            {t("missions.progress")}: {mission.progress_count}/{mission.required_count}
          </span>
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

        <div className="mt-auto flex flex-wrap gap-2">
          {mission.next_step ? (
            <Link href={mission.next_step.href} onClick={trackNextStep} className="pv-button-primary">
              {mission.next_step.label}
            </Link>
          ) : null}
          <Link href={`/missions/${mission.slug}`} className="pv-button-secondary">
            {t("dashboard.openMissionDetails")}
          </Link>
        </div>

        {mission.available_again_at ? (
          <p className="text-xs text-zinc-500">
            {t("missions.availableAgain")}: {new Date(mission.available_again_at).toLocaleString()}
          </p>
        ) : null}
      </div>
    </article>
  );
}

function getMissionTone(type: MissionType) {
  if (type === "progression") {
    return {
      badge: "border border-[rgba(37,92,255,0.18)] bg-[rgba(37,92,255,0.1)] text-[var(--pv-brand-strong)]",
      glow: "bg-[rgba(37,92,255,0.16)]",
    };
  }
  if (type === "learning") {
    return {
      badge: "border border-[rgba(17,184,164,0.18)] bg-[rgba(17,184,164,0.12)] text-[var(--pv-accent-strong)]",
      glow: "bg-[rgba(17,184,164,0.16)]",
    };
  }
  if (type === "action") {
    return {
      badge: "border border-[rgba(99,102,241,0.16)] bg-[rgba(99,102,241,0.1)] text-indigo-700",
      glow: "bg-[rgba(99,102,241,0.16)]",
    };
  }
  if (type === "streak") {
    return {
      badge: "border border-[rgba(245,158,11,0.18)] bg-[rgba(245,158,11,0.12)] text-amber-700",
      glow: "bg-[rgba(245,158,11,0.18)]",
    };
  }
  return {
    badge: "border border-[rgba(236,72,153,0.16)] bg-[rgba(236,72,153,0.1)] text-pink-700",
    glow: "bg-[rgba(236,72,153,0.16)]",
  };
}
