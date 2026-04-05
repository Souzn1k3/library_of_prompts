"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningStepSubmitResponse } from "@/lib/types";

type LearningWeakAreasPanelProps = {
  weakAreas: LearningStepSubmitResponse["weak_areas"];
};

export function LearningWeakAreasPanel({ weakAreas }: LearningWeakAreasPanelProps) {
  const { t } = useI18n();

  if (weakAreas.length === 0) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <p className="text-sm font-semibold text-zinc-900">{t("learn.recommendedFocus")}</p>
      <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
        {weakAreas.map((item) => (
          <li key={`${item.tag}-${item.lesson_slug ?? "none"}`}>• {item.recommendation}</li>
        ))}
      </ul>
    </section>
  );
}
