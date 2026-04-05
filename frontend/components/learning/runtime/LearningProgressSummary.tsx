"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";

type LearningProgressSummaryProps = {
  lessonProgressPercent: number;
  estimatedMinutes: number;
};

export function LearningProgressSummary({
  lessonProgressPercent,
  estimatedMinutes,
}: LearningProgressSummaryProps) {
  const { t } = useI18n();

  return (
    <div className="pv-panel px-6 py-5 sm:px-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm font-medium text-zinc-900">
          {t("learn.lessonProgress")}: {lessonProgressPercent}%
        </p>
        <p className="text-sm text-zinc-600">
          {t("learn.lessonEstimated")}: {estimatedMinutes}m
        </p>
      </div>
      <div
        className="mt-3 pv-progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={lessonProgressPercent}
      >
        <div className="pv-progress-fill" style={{ width: `${lessonProgressPercent}%` }} />
      </div>
    </div>
  );
}
