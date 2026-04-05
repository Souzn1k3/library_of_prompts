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

export type TextDraftDiagnostics = {
  wordCount: number;
  minWords: number;
  missingMarkers: string[];
  bonusHits: string[];
  forbiddenHits: string[];
};

function countWords(value: string): number {
  return value
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

export function evaluateTextDraft(step: LearningLessonStep, value: string): TextDraftDiagnostics {
  const normalized = value.toLowerCase();
  const minWords = step.min_words ?? 0;
  const requiredMarkers = step.required_markers ?? [];
  const bonusMarkers = step.bonus_markers ?? [];
  const forbiddenPhrases = step.forbidden_phrases ?? [];
  const missingMarkers = requiredMarkers.filter(
    (marker) => marker.trim().length > 0 && !normalized.includes(marker.toLowerCase()),
  );
  const bonusHits = bonusMarkers.filter(
    (marker) => marker.trim().length > 0 && normalized.includes(marker.toLowerCase()),
  );
  const forbiddenHits = forbiddenPhrases.filter(
    (phrase) => phrase.trim().length > 0 && normalized.includes(phrase.toLowerCase()),
  );

  return {
    wordCount: countWords(value),
    minWords,
    missingMarkers,
    bonusHits,
    forbiddenHits,
  };
}

export function recomputeStepUnlocks(steps: StepState[]): StepState[] {
  let canUnlockNextStep = true;
  return steps.map((step) => {
    const normalizedStep: StepState = {
      ...step,
      required_markers: step.required_markers ?? [],
      bonus_markers: step.bonus_markers ?? [],
      forbidden_phrases: step.forbidden_phrases ?? [],
    };
    const unlocked = canUnlockNextStep || normalizedStep.completed;
    if (!normalizedStep.completed) {
      canUnlockNextStep = false;
    }
    return { ...normalizedStep, unlocked };
  });
}
