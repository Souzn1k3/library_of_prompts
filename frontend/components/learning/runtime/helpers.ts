"use client";

import type { LearningLessonStep, LearningQuizQuestion } from "@/lib/types";

import type { LearningTranslation, StepState } from "@/components/learning/runtime/types";

export type StepChoiceAnswers = Record<string, Record<string, string>>;

const DEFAULT_QUIZ_QUESTION_ID = "default";

export function getQuizQuestions(
  step: Pick<LearningLessonStep, "question" | "choices" | "quiz_questions">,
): LearningQuizQuestion[] {
  if (Array.isArray(step.quiz_questions) && step.quiz_questions.length > 0) {
    return step.quiz_questions;
  }
  if (step.question && Array.isArray(step.choices) && step.choices.length > 0) {
    return [
      {
        id: DEFAULT_QUIZ_QUESTION_ID,
        question: step.question,
        choices: step.choices,
      },
    ];
  }
  return [];
}

export function buildInitialTextAnswers(steps: LearningLessonStep[]): Record<string, string> {
  return Object.fromEntries(
    steps.map((step) => [step.slug, step.last_answer_text && typeof step.last_answer_text === "string" ? step.last_answer_text : ""]),
  );
}

export function buildInitialChoiceAnswers(steps: LearningLessonStep[]): StepChoiceAnswers {
  const initialAnswers: StepChoiceAnswers = {};

  steps.forEach((step) => {
    const stepAnswers: Record<string, string> = {};

    if (step.last_choice_id && typeof step.last_choice_id === "string") {
      stepAnswers[DEFAULT_QUIZ_QUESTION_ID] = step.last_choice_id;
    }

    if (step.last_choice_map && typeof step.last_choice_map === "object") {
      Object.entries(step.last_choice_map).forEach(([questionId, choiceId]) => {
        if (typeof choiceId === "string" && choiceId.trim().length > 0) {
          stepAnswers[questionId] = choiceId;
        }
      });
    }

    initialAnswers[step.slug] = stepAnswers;
  });

  return initialAnswers;
}

export function extractErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
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
  choiceAnswers: StepChoiceAnswers,
  textAnswers: Record<string, string>,
): { choice_id: string } | { choice_ids: Record<string, string> } | { text: string } | null {
  if (step.submission_type === "choice") {
    const quizQuestions = getQuizQuestions(step);
    const stepAnswers = choiceAnswers[step.slug] ?? {};
    if (quizQuestions.length > 1) {
      return {
        choice_ids: Object.fromEntries(
          quizQuestions.map((question) => [question.id, stepAnswers[question.id] ?? ""]),
        ),
      };
    }
    return {
      choice_id: stepAnswers[quizQuestions[0]?.id ?? DEFAULT_QUIZ_QUESTION_ID] ?? "",
    };
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
  lowSignalMarkers: string[];
  looksLowSignal: boolean;
};

function countWords(value: string): number {
  return value
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function tokenize(value: string): string[] {
  return value.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
}

function alphaCharCount(value: string): number {
  return [...value].filter((char) => /\p{L}/u.test(char)).length;
}

function tokenSignalStats(value: string): {
  alphaRatio: number;
  longAlphaRatio: number;
  digitRatio: number;
} {
  const tokens = tokenize(value);
  if (tokens.length === 0) {
    return {
      alphaRatio: 0,
      longAlphaRatio: 0,
      digitRatio: 0,
    };
  }

  const alphaTokens = tokens.filter((token) => [...token].some((char) => /\p{L}/u.test(char)));
  const longAlphaTokens = alphaTokens.filter((token) => alphaCharCount(token) >= 3);
  const digitTokens = tokens.filter((token) => /^\d+$/u.test(token));

  return {
    alphaRatio: alphaTokens.length / tokens.length,
    longAlphaRatio: longAlphaTokens.length / tokens.length,
    digitRatio: digitTokens.length / tokens.length,
  };
}

function extractMarkerPayload(text: string, marker: string): string {
  const escapedMarker = marker.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = new RegExp(`${escapedMarker}\\s*[:\\-]?\\s*(.*?)(?=\\s*\\[[A-Z_]+\\]|$)`, "is").exec(text);
  return match?.[1]?.trim() ?? "";
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
  const lowSignalMarkers = requiredMarkers.filter((marker) => {
    if (marker.trim().length === 0 || !normalized.includes(marker.toLowerCase())) {
      return false;
    }
    const payload = extractMarkerPayload(value, marker);
    if (countWords(payload) < 3) {
      return false;
    }
    const stats = tokenSignalStats(payload);
    return stats.alphaRatio < 0.55 || stats.longAlphaRatio < 0.35 || stats.digitRatio > 0.35;
  });
  const overallStats = tokenSignalStats(value);
  const looksLowSignal =
    countWords(value) >= Math.max(minWords, 10) &&
    (overallStats.alphaRatio < 0.72 || overallStats.longAlphaRatio < 0.45 || overallStats.digitRatio > 0.2);

  return {
    wordCount: countWords(value),
    minWords,
    missingMarkers,
    bonusHits,
    forbiddenHits,
    lowSignalMarkers,
    looksLowSignal,
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
      quiz_questions: step.quiz_questions ?? [],
      last_choice_map: step.last_choice_map ?? {},
    };
    const unlocked = canUnlockNextStep || normalizedStep.completed;
    if (!normalizedStep.completed) {
      canUnlockNextStep = false;
    }
    return { ...normalizedStep, unlocked };
  });
}
