"use client";

import { useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  MissionsHero,
  type MissionCollectionView,
} from "@/components/missions/MissionsHero";
import { MissionsSectionList } from "@/components/missions/MissionsSectionList";
import {
  MissionsEmptyView,
  MissionsErrorView,
  MissionsLoadingView,
  MissionsUnauthenticatedView,
} from "@/components/missions/MissionsStatusViews";
import { useMissionsData } from "@/components/missions/useMissionsData";
import { useMissionsViewModel } from "@/components/missions/useMissionsViewModel";
import { EconomyLoop } from "@/components/navigation/EconomyLoop";

export function MissionsClient() {
  const { t, language } = useI18n();
  const [selectedView, setSelectedView] = useState<MissionCollectionView>("active");
  const { data, error, loading, reload } = useMissionsData({
    language,
    loadFailedMessage: t("missions.loadFailed"),
  });
  const { currentMission, nextMission, latestCompleted, filterCounts, sections } =
    useMissionsViewModel({
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

      <MissionsSectionList sections={sections} t={t} />
    </div>
  );
}
