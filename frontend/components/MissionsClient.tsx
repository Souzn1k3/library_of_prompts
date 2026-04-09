"use client";

import Link from "next/link";
import { useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  type MissionCollectionView,
} from "@/components/missions/MissionsHero";
import {
  MissionsEmptyView,
  MissionsErrorView,
  MissionsLoadingView,
  MissionsUnauthenticatedView,
} from "@/components/missions/MissionsStatusViews";
import { useMissionsData } from "@/components/missions/useMissionsData";
import { useMissionsViewModel } from "@/components/missions/useMissionsViewModel";
import { appRoute } from "@/lib/constants/routes";
import type { MissionListRead } from "@/lib/types";

type MissionsClientProps = {
  initialData?: MissionListRead | null;
  initialError?: "signed_out" | string | null;
};

export function MissionsClient({ initialData = null, initialError = null }: MissionsClientProps) {
  const { t, language } = useI18n();
  const [selectedView, setSelectedView] = useState<MissionCollectionView>("active");
  const { data, error, loading, reload } = useMissionsData({
    language,
    loadFailedMessage: t("missions.loadFailed"),
    initialData,
    initialError,
  });
  const { currentMission, nextMission, filterCounts, sections } = useMissionsViewModel({
    data,
    language,
    selectedView,
  });

  if (error === "signed_out") {
    return <MissionsUnauthenticatedView t={t} />;
  }

  if (error) {
    return <MissionsErrorView t={t} error={error} onReload={reload} />;
  }

  if (loading || !data) {
    return <MissionsLoadingView t={t} />;
  }

  if (data.missions.length === 0) {
    return <MissionsEmptyView t={t} />;
  }

  return (
    <div className="space-y-6">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] xl:items-start">
          <div className="space-y-4">
            <p className="pv-kicker">{t("missions.title")}</p>
            <h1 className="text-4xl font-semibold tracking-[-0.06em] text-zinc-950 sm:text-5xl">
              {currentMission?.title ?? t("missions.title")}
            </h1>
            <p className="pv-lead">{currentMission?.objective ?? t("missions.subtitle")}</p>
            <div className="pv-cta-group">
              {currentMission?.nextStep ? (
                <Link href={currentMission.nextStep.href} className="pv-button-primary !w-auto">
                  {currentMission.nextStep.label}
                </Link>
              ) : null}
              {currentMission ? (
                <Link
                  href={appRoute.missionBySlug(currentMission.mission.slug)}
                  className="pv-button-secondary !w-auto"
                >
                  {t("missions.openMissionDetails")}
                </Link>
              ) : null}
            </div>
          </div>

          <div className="grid gap-3">
            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missions.progress")}</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-zinc-950">
                {data.completed_count}/{data.total_count}
              </p>
            </div>
            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missions.credits")}</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-zinc-950">
                +{data.rewards.credits}
              </p>
            </div>
            <div className="rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missions.heroNext")}</p>
              <p className="mt-2 text-lg font-semibold tracking-[-0.04em] text-zinc-950">
                {nextMission?.title ?? t("missions.title")}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="pv-panel px-5 py-5 sm:px-6">
        <div className="flex flex-wrap gap-2">
          {([
            { value: "active", count: filterCounts.active },
            { value: "in_progress", count: filterCounts.in_progress },
            { value: "repeatable", count: filterCounts.repeatable },
          ] as const).map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => setSelectedView(filter.value)}
              className={`rounded-[1rem] border px-4 py-2 text-sm font-semibold transition ${
                selectedView === filter.value
                  ? "border-[var(--pv-brand)]/35 bg-[var(--pv-brand-soft)] text-zinc-950"
                  : "border-[var(--pv-border)] bg-white/74 text-zinc-600"
              }`}
            >
              {t(`missions.heroFilter.${filter.value}`)} · {filter.count}
            </button>
          ))}
        </div>
      </section>

      {sections.map((section) => (
        <section key={section.type} className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("missions.title")}</p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">
                {t(`missions.type.${section.type}`)}
              </h2>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            {section.items.map((mission) => {
              const progress = Math.round(
                (mission.mission.progress_count / Math.max(1, mission.mission.required_count)) * 100,
              );

              return (
                <article
                  key={mission.mission.id}
                  className="rounded-[1.45rem] border border-[var(--pv-border)] bg-white/78 p-5"
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="pv-chip-brand">{t(`missions.type.${mission.mission.mission_type}`)}</span>
                        <span className="pv-chip">{t(`missions.status.${mission.mission.status}`)}</span>
                        {mission.mission.is_repeatable ? <span className="pv-chip">{t("missions.repeatable")}</span> : null}
                      </div>
                      <h3 className="text-xl font-semibold tracking-[-0.04em] text-zinc-950">{mission.title}</h3>
                      <p className="text-sm leading-relaxed text-zinc-600">{mission.objective}</p>
                    </div>

                    <div className="min-w-[10rem] rounded-[1.2rem] border border-[var(--pv-border)] bg-white/72 px-4 py-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missions.credits")}</p>
                      <p className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
                        +{mission.mission.reward.credits}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between gap-3 text-sm text-zinc-600">
                      <span>{mission.mission.progress_count}/{mission.mission.required_count}</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="pv-progress">
                      <div className="pv-progress-fill" style={{ width: `${progress}%` }} />
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-3">
                    {mission.nextStep ? (
                      <Link href={mission.nextStep.href} className="pv-button-primary !w-auto">
                        {mission.nextStep.label}
                      </Link>
                    ) : null}
                    <Link href={appRoute.missionBySlug(mission.mission.slug)} className="pv-button-secondary !w-auto">
                      {t("missions.openMissionDetails")}
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
