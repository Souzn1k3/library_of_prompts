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
          <p className="pv-kicker">{t("nav.missions")}</p>
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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="pv-kicker">{t("missions.title")}</p>
        <span className="pv-chip-brand">
          {sections.reduce((acc, section) => acc + section.items.length, 0)}
        </span>
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

      <div className="mt-6 space-y-8">
        {sections.map((section, index) => (
          <div key={section.type} className={index > 0 ? "border-t border-[var(--pv-border)] pt-8" : ""}>
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
          </div>
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
      className={active ? "pv-button-primary !w-auto" : "pv-button-secondary !w-auto"}
    >
      {label}
      <span className="ml-2 rounded-full bg-black/10 px-2 py-0.5 text-[11px] font-semibold">
        {count}
      </span>
    </button>
  );
}
