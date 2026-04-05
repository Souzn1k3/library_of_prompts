"use client";

import type { LearningLessonStep, LearningStepFeedback } from "@/lib/types";

export type StepState = LearningLessonStep & {
  feedback?: LearningStepFeedback | null;
};

export type LearningTranslation = (
  key: string,
  params?: Record<string, string | number | null | undefined>,
) => string;
