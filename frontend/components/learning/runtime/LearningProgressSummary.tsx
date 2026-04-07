"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";

type LearningProgressSummaryProps = {
  lessonProgressPercent: number;
  courseProgressPercent: number;
  estimatedMinutes: number;
  stepsCount: number;
  completedStepsCount: number;
  activeStepIndex: number;
};

function Metric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-[var(--pv-border)] bg-white/90 px-3 py-1 text-xs text-zinc-700">
      <span className="font-semibold uppercase tracking-[0.08em] text-zinc-500">{label}</span>
      <span className="font-semibold text-zinc-950">{value}</span>
    </span>
  );
}

export function LearningProgressSummary({
  lessonProgressPercent,
  courseProgressPercent,
  estimatedMinutes,
  stepsCount,
  completedStepsCount,
  activeStepIndex,
}: LearningProgressSummaryProps) {
  const { t } = useI18n();
  const remainingSteps = Math.max(stepsCount - completedStepsCount, 0);

  return (
    <div className="pv-panel px-4 py-3 sm:px-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="pv-chip-brand">
          {t("learn.stepPosition", { current: activeStepIndex + 1, total: stepsCount })}
        </span>
        <span className="inline-flex items-center rounded-full border border-[var(--pv-border)] bg-white/90 px-3 py-1 text-xs font-semibold text-zinc-950">
          {courseProgressPercent}%
        </span>
        <Metric label={t("learn.lessonProgress")} value={`${lessonProgressPercent}%`} />
        <Metric label={t("learn.lessonEstimated")} value={`${estimatedMinutes}m`} />
      </div>

      <div
        className="mt-2 pv-progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={lessonProgressPercent}
      >
        <div className="pv-progress-fill" style={{ width: `${lessonProgressPercent}%` }} />
      </div>

      <p className="mt-2 text-xs text-zinc-600">
        {t("learn.remainingStepsHint", { count: remainingSteps })}
      </p>
    </div>
  );
}
