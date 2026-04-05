import { cache } from "react";

import { fetchLearningCourse } from "@/lib/api";
import { appRoute } from "@/lib/constants/routes";
import type { Language } from "@/lib/i18n";
import type { LearningCourseDetail } from "@/lib/types";

export type LearningCoursePageData = {
  course: LearningCourseDetail;
  primaryHref: string;
};

export const getLearningCourseCached = cache(
  async (courseSlug: string, accessToken: string | null | undefined, language: Language) =>
    fetchLearningCourse(courseSlug, accessToken, language),
);

export async function loadLearningCoursePageData({
  courseSlug,
  accessToken,
  language,
}: {
  courseSlug: string;
  accessToken: string | null | undefined;
  language: Language;
}): Promise<LearningCoursePageData> {
  const course = await getLearningCourseCached(courseSlug, accessToken, language);
  const firstLesson = course.modules[0]?.lessons[0];
  const primaryHref = course.resume_href ?? (firstLesson ? firstLesson.continue_href : appRoute.learnCourse(courseSlug));

  return {
    course,
    primaryHref,
  };
}
