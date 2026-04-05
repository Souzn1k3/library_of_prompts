"use client";

import type { LearningLessonStep } from "@/lib/types";

import type { LearningTranslation, StepState } from "@/components/learning/runtime/types";

export function buildInitialTextAnswers(steps: LearningLessonStep[]): Record<string, string> {
  return Object.fromEntries(steps.map((step) => [step.slug, ""]));
}

export function extractErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return "Could not submit this step. Please try again.";
}

export function suggestedTemplate(step: LearningLessonStep, t: LearningTranslation): string | null {
  if (step.placeholder && step.placeholder.trim().length > 0) {
    return step.placeholder.trim();
  }
  if (step.kind === "guided_practice") {
    return t("learn.templateGuided");
  }
  if (step.kind === "applied_exercise") {
    return t("learn.templateApplied");
  }
  if (step.kind === "reflection") {
    return t("learn.templateReflection");
  }
  return null;
}

export function buildSubmissionAnswer(
  step: StepState,
  choiceAnswers: Record<string, string>,
  textAnswers: Record<string, string>,
): { choice_id: string } | { text: string } | null {
  if (step.submission_type === "choice") {
    return { choice_id: choiceAnswers[step.slug] ?? "" };
  }
  if (step.submission_type === "text") {
    return { text: textAnswers[step.slug] ?? "" };
  }
  return null;
}
