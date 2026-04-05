import { cache } from "react";

import { fetchLearningCourse, fetchLearningLesson } from "@/lib/api";
import type { Language } from "@/lib/i18n";
import type { LearningCourseDetail, LearningLessonDetail, LearningLessonStep } from "@/lib/types";

export type LearningLessonStepPageData = {
  lesson: LearningLessonDetail;
  course: LearningCourseDetail;
  step: LearningLessonStep;
  previousStep: LearningLessonStep | null;
  nextStep: LearningLessonStep | null;
  stepIndex: number;
  canSubmit: boolean;
};

export const getLearningLessonCached = cache(
  async (
    courseSlug: string,
    lessonSlug: string,
    accessToken: string | null | undefined,
    language: Language,
  ) => fetchLearningLesson(courseSlug, lessonSlug, accessToken, language),
);

export async function loadLearningLessonStepPageData({
  courseSlug,
  lessonSlug,
  stepSlug,
  accessToken,
  language,
}: {
  courseSlug: string;
  lessonSlug: string;
  stepSlug: string;
  accessToken: string | null | undefined;
  language: Language;
}): Promise<LearningLessonStepPageData | null> {
  const [lesson, course] = await Promise.all([
    getLearningLessonCached(courseSlug, lessonSlug, accessToken, language),
    fetchLearningCourse(courseSlug, accessToken, language),
  ]);

  const stepIndex = lesson.steps.findIndex((step) => step.slug === stepSlug);
  if (stepIndex < 0) {
    return null;
  }

  return {
    lesson,
    course,
    step: lesson.steps[stepIndex],
    previousStep: stepIndex > 0 ? lesson.steps[stepIndex - 1] : null,
    nextStep: stepIndex < lesson.steps.length - 1 ? lesson.steps[stepIndex + 1] : null,
    stepIndex,
    canSubmit: Boolean(accessToken),
  };
}
