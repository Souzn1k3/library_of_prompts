"use client";

import { MissionCard } from "@/components/missions/MissionCard";
import { type MissionCollectionView } from "@/components/missions/MissionsHero";
import type { MissionSectionView } from "@/components/missions/useMissionsViewModel";
import { type TranslationKey } from "@/lib/i18n";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type MissionsSectionListProps = {
  sections: MissionSectionView[];
  t: Translate;
  selectedView: MissionCollectionView;
  onSelectView: (view: MissionCollectionView) => void;
  filterCounts: Record<MissionCollectionView, number>;
};

export function MissionsSectionList({
  sections,
  t,
  selectedView,
  onSelectView,
  filterCounts,
}: MissionsSectionListProps) {
  const missionFeed = sections.flatMap((section) => section.items);

  if (sections.length === 0) {
    return (
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="mb-5 flex flex-wrap gap-2">
          <FilterButton
            active={selectedView === "active"}
            label={t("missions.heroFilter.active")}
            count={filterCounts.active}
            onClick={() => onSelectView("active")}
          />
          <FilterButton
            active={selectedView === "in_progress"}
            label={t("missions.heroFilter.in_progress")}
            count={filterCounts.in_progress}
            onClick={() => onSelectView("in_progress")}
          />
          <FilterButton
            active={selectedView === "repeatable"}
            label={t("missions.heroFilter.repeatable")}
            count={filterCounts.repeatable}
            onClick={() => onSelectView("repeatable")}
          />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("missions.filteredEmptyTitle")}
          </h2>
          <p className="text-sm leading-relaxed text-zinc-600">{t("missions.filteredEmptyBody")}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("missions.title")}</h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("missions.subtitle")}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <FilterButton
          active={selectedView === "active"}
          label={t("missions.heroFilter.active")}
          count={filterCounts.active}
          onClick={() => onSelectView("active")}
        />
        <FilterButton
          active={selectedView === "in_progress"}
          label={t("missions.heroFilter.in_progress")}
          count={filterCounts.in_progress}
          onClick={() => onSelectView("in_progress")}
        />
        <FilterButton
          active={selectedView === "repeatable"}
          label={t("missions.heroFilter.repeatable")}
          count={filterCounts.repeatable}
          onClick={() => onSelectView("repeatable")}
        />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        {missionFeed.map((mission) => (
          <MissionCard key={mission.mission.id} mission={mission} />
        ))}
      </div>
    </section>
  );
}

function FilterButton({
  active,
  label,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-[0.95rem] border px-4 py-2 text-sm font-semibold transition ${
        active
          ? "border-[var(--pv-brand)] bg-[var(--pv-brand)] text-white"
          : "border-[var(--pv-border)] bg-white text-zinc-700 hover:border-[var(--pv-border-strong)]"
      }`}
    >
      {label}
      <span
        className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
          active ? "bg-white/20 text-white" : "bg-zinc-100 text-zinc-600"
        }`}
      >
        {count}
      </span>
    </button>
  );
}
