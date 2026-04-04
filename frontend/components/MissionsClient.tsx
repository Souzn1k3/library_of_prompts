"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  MissionsHero,
  type MissionCollectionView,
} from "@/components/missions/MissionsHero";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { trackEvent } from "@/lib/analytics";
import { ApiRequestError } from "@/lib/api";
import { fetchMissions } from "@/lib/client-api";
import { MISSION_SECTION_ORDER, MISSION_TYPE_TONE } from "@/lib/constants/economy-ui";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { getMissionStatusTranslationKey, type TranslationKey } from "@/lib/i18n";
import {
  formatMissionDateTime,
  getMissionPresentation,
  type MissionPresentation,
} from "@/lib/missionPresentation";
import type { MissionListRead } from "@/lib/types";

export function MissionsClient() {
  const { t, language } = useI18n();
  const [data, setData] = useState<MissionListRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);
  const [selectedView, setSelectedView] = useState<MissionCollectionView>("active");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchMissions()
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
        setError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setData(null);
        if (e instanceof ApiRequestError && e.status === 401) {
          setError("signed_out");
        } else {
          setError(e instanceof Error ? e.message : t("missions.loadFailed"));
        }
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [language, reloadToken, t]);

  const localizedMissions = useMemo(
    () => data?.missions.map((mission) => getMissionPresentation(language, mission)) ?? [],
    [data, language],
  );

  const currentMission = useMemo(() => {
    if (!data) {
      return null;
    }

    if (!data.current_mission_slug) {
      return localizedMissions.find((mission) => mission.mission.status === "in_progress") ?? null;
    }

    return (
      localizedMissions.find((mission) => mission.mission.slug === data.current_mission_slug) ?? null
    );
  }, [data, localizedMissions]);

  const nextMission = useMemo(
    () =>
      localizedMissions.find(
        (mission) =>
          mission.mission.slug !== currentMission?.mission.slug &&
          mission.mission.status !== "completed",
      ) ?? null,
    [currentMission, localizedMissions],
  );

  const latestCompleted = useMemo(() => {
    const completed = localizedMissions
      .filter((mission) => mission.mission.completed_at)
      .sort((left, right) => {
        const leftTime = left.mission.completed_at ? new Date(left.mission.completed_at).getTime() : 0;
        const rightTime = right.mission.completed_at ? new Date(right.mission.completed_at).getTime() : 0;
        return rightTime - leftTime;
      });

    return completed[0] ?? null;
  }, [localizedMissions]);

  const filterCounts = useMemo(
    () => ({
      active: localizedMissions.filter((mission) => mission.mission.status !== "completed").length,
      in_progress: localizedMissions.filter((mission) => mission.mission.status === "in_progress").length,
      repeatable: localizedMissions.filter((mission) => mission.mission.is_repeatable).length,
    }),
    [localizedMissions],
  );

  const filteredMissions = useMemo(() => {
    if (selectedView === "in_progress") {
      return localizedMissions.filter((mission) => mission.mission.status === "in_progress");
    }
    if (selectedView === "repeatable") {
      return localizedMissions.filter((mission) => mission.mission.is_repeatable);
    }
    return localizedMissions.filter((mission) => mission.mission.status !== "completed");
  }, [localizedMissions, selectedView]);

  const sections = useMemo(() => {
    if (!data) return [];

    return MISSION_SECTION_ORDER.map((type) => ({
      type,
      items: filteredMissions.filter((mission) => mission.mission.mission_type === type),
    })).filter((section) => section.items.length > 0);
  }, [data, filteredMissions]);

  if (error === "signed_out") {
    return (
      <div className="space-y-6">
        <PageIntro
          eyebrow={t("nav.missions")}
          title={t("missions.title")}
          description={t("missions.subtitle")}
          hint={t("missions.guestHint")}
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.catalog} className="pv-inline-link">
                {t("home.explorePrompts")}
                <span aria-hidden="true">↗</span>
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("missions.signInPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
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
              <Link href={APP_ROUTES.catalog} className="pv-button-primary">
                {t("home.explorePrompts")}
              </Link>
              <Link href={APP_ROUTES.dashboard} className="pv-button-secondary">
                {t("nav.dashboard")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">{t("missions.empty")}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <MissionsHero
        currentMission={currentMission}
        nextMission={nextMission}
        latestCompleted={latestCompleted}
        selectedView={selectedView}
        onSelectView={setSelectedView}
        filterCounts={filterCounts}
        completedCount={data.completed_count}
        totalCount={data.total_count}
        rewardCredits={data.rewards.credits}
        rewardBadgeCount={data.rewards.badges.length}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <EconomyLoop />
      </section>

      {sections.length === 0 ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="space-y-2">
            <p className="pv-kicker">{t("nav.missions")}</p>
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              {t("missions.filteredEmptyTitle")}
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">{t("missions.filteredEmptyBody")}</p>
          </div>
        </section>
      ) : null}

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
          <div className={`mt-6 grid gap-4 ${section.items.length > 1 ? "xl:grid-cols-2" : ""}`}>
            {section.items.map((mission) => (
              <MissionCard key={mission.mission.id} mission={mission} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function MissionCard({ mission }: { mission: MissionPresentation }) {
  const { t, language } = useI18n();
  const pct = Math.round(
    (mission.mission.progress_count / Math.max(1, mission.mission.required_count)) * 100,
  );
  const tone = MISSION_TYPE_TONE[mission.mission.mission_type];

  function trackNextStep() {
    if (!mission.nextStep) return;
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: APP_ROUTES.missions,
      feature: "mission_loop",
      metadata: {
        mission_id: mission.mission.id,
        mission_slug: mission.mission.slug,
        status: mission.mission.status,
        progress_count: mission.mission.progress_count,
        required_count: mission.mission.required_count,
        action: mission.nextStep.action,
        href: mission.nextStep.href,
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
                {t(`missions.type.${mission.mission.mission_type}` as TranslationKey)}
              </span>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  mission.mission.status === "completed"
                    ? "bg-emerald-100 text-emerald-900"
                    : mission.mission.status === "in_progress"
                      ? "bg-blue-100 text-blue-900"
                      : "bg-zinc-100 text-zinc-700"
                }`}
              >
                {t(getMissionStatusTranslationKey(mission.mission.status))}
              </span>
              {mission.mission.is_repeatable ? <span className="pv-badge">{t("missions.repeatable")}</span> : null}
              {mission.mission.chain_id ? (
                <span className="pv-badge">
                  {t("missions.chainProgress", {
                    step: mission.mission.chain_step,
                    total: mission.mission.chain_total || 1,
                  })}
                </span>
              ) : null}
            </div>
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{mission.title}</h3>
            <p className="text-sm leading-relaxed text-zinc-600">{mission.objective}</p>
            {mission.mission.adaptive_reason ? (
              <p className="text-xs text-zinc-500">
                {t("missions.adaptiveReason", { reason: mission.mission.adaptive_reason })}
              </p>
            ) : null}
          </div>

          {mission.mission.reward.credits > 0 ? (
            <LmnAmount amount={`+${mission.mission.reward.credits}`} symbol={TOKEN_SHORT_CODE} state="earned" strong />
          ) : null}
        </div>

        <div className="pv-progress">
          <div className="pv-progress-fill" style={{ width: `${pct}%` }} />
        </div>

        <div className="flex flex-wrap gap-3 text-xs text-zinc-500">
          <span>
            {t("missions.progress")}: {mission.mission.progress_count}/{mission.mission.required_count}
          </span>
          {mission.badgeLabel ? (
            <span>
              {t("missions.badge")}: {mission.badgeLabel}
            </span>
          ) : null}
          {mission.mission.completion_count > 0 ? (
            <span>
              {t("missions.completedTimes")}: {mission.mission.completion_count}
            </span>
          ) : null}
        </div>

        <div className="mt-auto flex flex-wrap gap-2">
          {mission.nextStep ? (
            <Link href={mission.nextStep.href} onClick={trackNextStep} className="pv-button-primary">
              {mission.nextStep.label}
            </Link>
          ) : null}
          <Link href={appRoute.missionBySlug(mission.mission.slug)} className="pv-button-secondary">
            {t("missions.openMissionDetails")}
          </Link>
        </div>

        {mission.mission.available_again_at ? (
          <p className="text-xs text-zinc-500">
            {t("missions.availableAgain")}: {formatMissionDateTime(language, mission.mission.available_again_at)}
          </p>
        ) : null}
      </div>
    </article>
  );
}
