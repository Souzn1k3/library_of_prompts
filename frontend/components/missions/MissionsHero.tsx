"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { getMissionStatusTranslationKey, type TranslationKey } from "@/lib/i18n";
import type { MissionPresentation } from "@/lib/missionPresentation";

export type MissionCollectionView = "active" | "in_progress" | "repeatable";

type MissionsHeroProps = {
  currentMission: MissionPresentation | null;
  nextMission: MissionPresentation | null;
  latestCompleted: MissionPresentation | null;
  completedCount: number;
  totalCount: number;
  rewardCredits: number;
  rewardBadgeCount: number;
};

export function MissionsHero({
  currentMission,
  nextMission,
  latestCompleted,
  completedCount,
  totalCount,
  rewardCredits,
  rewardBadgeCount,
}: MissionsHeroProps) {
  const { t } = useI18n();

  return (
    <PageIntro
      eyebrow={t("nav.missions")}
      title={t("missions.title")}
      description={t("missions.subtitle")}
    >
      <div className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="pv-card-muted pv-catalog-filter-card-white p-4">
            <p className="pv-stat-label">{t("missions.progress")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
              {completedCount}/{totalCount}
            </p>
          </div>
          <div className="pv-card-muted pv-catalog-filter-card-white p-4">
            <p className="pv-stat-label">{t("missions.credits")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{rewardCredits}</p>
          </div>
          <div className="pv-card-muted pv-catalog-filter-card-white p-4">
            <p className="pv-stat-label">{t("missions.badges")}</p>
            <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{rewardBadgeCount}</p>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-3">
          <MissionNavCard
            label={t("missions.heroCurrent")}
            mission={currentMission}
            emptyText={t("missions.heroNoneCurrent")}
            ctaLabel={currentMission?.nextStep?.label ?? t("missions.openMission")}
            href={currentMission?.nextStep?.href ?? (currentMission ? `/missions/${currentMission.mission.slug}` : null)}
          />
          <MissionNavCard
            label={t("missions.heroNext")}
            mission={nextMission}
            emptyText={t("missions.heroNoneNext")}
            ctaLabel={t("missions.openMission")}
            href={nextMission ? `/missions/${nextMission.mission.slug}` : null}
          />
          <MissionNavCard
            label={t("missions.heroLatest")}
            mission={latestCompleted}
            emptyText={t("missions.heroNoneLatest")}
            ctaLabel={t("missions.nextStep.viewResult")}
            href={latestCompleted ? `/missions/${latestCompleted.mission.slug}` : null}
          />
        </div>
      </div>
    </PageIntro>
  );
}

function MissionNavCard({
  label,
  mission,
  emptyText,
  ctaLabel,
  href,
}: {
  label: string;
  mission: MissionPresentation | null;
  emptyText: string;
  ctaLabel: string;
  href: string | null;
}) {
  const { t } = useI18n();

  return (
    <article className="pv-card-muted pv-catalog-filter-card-white flex h-full flex-col gap-4 p-4">
      <div className="space-y-2">
        <p className="pv-stat-label">{label}</p>
        {mission ? (
          <>
            <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{mission.title}</h2>
            <p className="text-sm leading-relaxed text-zinc-600">{mission.objective}</p>
          </>
        ) : (
          <p className="text-sm leading-relaxed text-zinc-600">{emptyText}</p>
        )}
      </div>

      {mission ? (
        <div className="flex flex-wrap gap-2">
          <span className="pv-badge-brand">
            {t(`missions.type.${mission.mission.mission_type}` as TranslationKey)}
          </span>
          <span className="pv-badge">
            {t(getMissionStatusTranslationKey(mission.mission.status))}
          </span>
          <span className="pv-badge">
            {mission.mission.progress_count}/{mission.mission.required_count}
          </span>
        </div>
      ) : null}

      {href ? (
        <Link href={href} className="mt-auto pv-inline-link">
          {ctaLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      ) : null}
    </article>
  );
}
