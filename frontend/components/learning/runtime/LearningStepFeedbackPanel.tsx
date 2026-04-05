"use client";

import type { StepState } from "@/components/learning/runtime/types";

type LearningStepFeedbackPanelProps = {
  step: StepState;
};

export function LearningStepFeedbackPanel({ step }: LearningStepFeedbackPanelProps) {
  if (!step.feedback) {
    return null;
  }

  return (
    <div className="mt-4 rounded-[1rem] border border-emerald-200 bg-emerald-50/70 p-4 text-sm text-emerald-950">
      <p className="font-semibold">
        {step.feedback.verdict} · {step.feedback.score}/100
      </p>
      {step.feedback.strengths.length > 0 ? (
        <ul className="mt-2 grid gap-1 text-emerald-900">
          {step.feedback.strengths.map((item) => (
            <li key={`${step.slug}-strength-${item}`}>• {item}</li>
          ))}
        </ul>
      ) : null}
      {step.feedback.improvements.length > 0 ? (
        <ul className="mt-2 grid gap-1 text-amber-900">
          {step.feedback.improvements.map((item) => (
            <li key={`${step.slug}-improvement-${item}`}>• {item}</li>
          ))}
        </ul>
      ) : null}
      {step.feedback.revisit.length > 0 ? (
        <ul className="mt-2 grid gap-1 text-zinc-800">
          {step.feedback.revisit.map((item) => (
            <li key={`${step.slug}-revisit-${item}`}>• {item}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
