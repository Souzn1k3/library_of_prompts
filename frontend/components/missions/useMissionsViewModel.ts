"use client";

import { useMemo } from "react";

import type { MissionCollectionView } from "@/components/missions/MissionsHero";
import { MISSION_SECTION_ORDER } from "@/lib/constants/economy-ui";
import {
  getMissionPresentation,
  type MissionPresentation,
} from "@/lib/missionPresentation";
import type { Language } from "@/lib/i18n";
import type { MissionListRead, MissionType } from "@/lib/types";

type UseMissionsViewModelArgs = {
  data: MissionListRead | null;
  language: Language;
  selectedView: MissionCollectionView;
};

export type MissionSectionView = {
  type: MissionType;
  items: MissionPresentation[];
};

export function useMissionsViewModel({
  data,
  language,
  selectedView,
}: UseMissionsViewModelArgs) {
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
    return localizedMissions.find((mission) => mission.mission.slug === data.current_mission_slug) ?? null;
  }, [data, localizedMissions]);

  const nextMission = useMemo(
    () =>
      localizedMissions.find(
        (mission) =>
          mission.mission.slug !== currentMission?.mission.slug &&
          mission.mission.status !== "completed",
      ) ?? null,
    [currentMission?.mission.slug, localizedMissions],
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

  const sections = useMemo<MissionSectionView[]>(() => {
    if (!data) {
      return [];
    }
    return MISSION_SECTION_ORDER.map((type) => ({
      type,
      items: filteredMissions.filter((mission) => mission.mission.mission_type === type),
    })).filter((section) => section.items.length > 0);
  }, [data, filteredMissions]);

  return {
    localizedMissions,
    currentMission,
    nextMission,
    latestCompleted,
    filterCounts,
    filteredMissions,
    sections,
  };
}
