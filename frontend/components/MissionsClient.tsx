"use client";

import { useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { type MissionCollectionView } from "@/components/missions/MissionsHero";
import { MissionsSectionList } from "@/components/missions/MissionsSectionList";
import {
  MissionsEmptyView,
  MissionsErrorView,
  MissionsLoadingView,
  MissionsUnauthenticatedView,
} from "@/components/missions/MissionsStatusViews";
import { useMissionsData } from "@/components/missions/useMissionsData";
import { useMissionsViewModel } from "@/components/missions/useMissionsViewModel";
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
  const { filterCounts, sections } = useMissionsViewModel({
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
      <MissionsSectionList
        sections={sections}
        t={t}
        selectedView={selectedView}
        onSelectView={setSelectedView}
        filterCounts={filterCounts}
      />
    </div>
  );
}
