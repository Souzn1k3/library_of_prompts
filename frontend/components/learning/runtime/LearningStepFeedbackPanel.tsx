"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { StepState } from "@/components/learning/runtime/types";

type LearningStepFeedbackPanelProps = {
  step: StepState;
};

function FeedbackList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-[0.12em]">{title}</p>
      <ul className="mt-2 grid gap-1 text-sm">
        {items.map((item) => (
          <li key={`${title}-${item}`}>• {item}</li>
        ))}
      </ul>
    </section>
  );
}

export function LearningStepFeedbackPanel({ step }: LearningStepFeedbackPanelProps) {
  const { t } = useI18n();
  if (!step.feedback) {
    return null;
  }

  const passed = step.feedback.score >= step.feedback.pass_score;
  const panelClass = passed
    ? "mt-5 rounded-[1rem] border border-emerald-200 bg-emerald-50/80 p-4 text-emerald-950"
    : "mt-5 rounded-[1rem] border border-amber-200 bg-amber-50/80 p-4 text-amber-950";

  return (
    <div className={panelClass}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold">{passed ? t("learn.completed") : t("learn.stepNeedsRevision")}</p>
        <p className="text-sm font-semibold">
          {t("learn.feedbackScoreOnly", { score: step.feedback.score })}
        </p>
      </div>
      <div className="mt-3 grid gap-3">
        <FeedbackList title={t("learn.feedbackStrengths")} items={step.feedback.strengths} />
        <FeedbackList title={t("learn.feedbackImprovements")} items={step.feedback.improvements} />
        <FeedbackList title={t("learn.feedbackRevisit")} items={step.feedback.revisit} />
      </div>
      {step.feedback.hint ? (
        <p className="mt-3 text-sm">
          <span className="font-semibold">{t("learn.feedbackHint")}: </span>
          {step.feedback.hint}
        </p>
      ) : null}
    </div>
  );
}

