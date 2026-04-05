"use client";

import { MissionCard } from "@/components/missions/MissionCard";
import type { MissionSectionView } from "@/components/missions/useMissionsViewModel";
import { type TranslationKey } from "@/lib/i18n";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type MissionsSectionListProps = {
  sections: MissionSectionView[];
  t: Translate;
};

export function MissionsSectionList({ sections, t }: MissionsSectionListProps) {
  if (sections.length === 0) {
    return (
      <section className="pv-panel px-6 py-6 sm:px-7">
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
    <>
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
    </>
  );
}
