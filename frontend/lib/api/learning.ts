import { API_ENDPOINTS, apiPath } from "../constants/api";
import { withQuery } from "../http";
import type {
  LearningCatalog,
  LearningCourseDetail,
  LearningLessonDetail,
  LearningMyModules,
  LearningStartTarget,
  LearningStepSubmitResponse,
  LessonDetail,
  LessonListItem,
  PopularLessonItem,
} from "../types";
import type { Language } from "../i18n";
import { apiFetch } from "./transport";

export async function fetchLessons(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LessonListItem[]> {
  return apiFetch<LessonListItem[]>(API_ENDPOINTS.lessons, { accessToken, language });
}

export async function fetchPopularLessons(
  params?: {
    limit?: number;
    accessToken?: string | null;
    language?: Language | string | null;
  },
): Promise<PopularLessonItem[]> {
  return apiFetch<PopularLessonItem[]>(withQuery(API_ENDPOINTS.lessonsPopular, { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}

export async function fetchLessonBySlug(
  slug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LessonDetail> {
  return apiFetch<LessonDetail>(apiPath.lessonBySlug(slug), {
    accessToken,
    language,
  });
}

export async function fetchLearningStartTarget(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningStartTarget> {
  return apiFetch<LearningStartTarget>(API_ENDPOINTS.learningStartTarget, {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function fetchLearningCatalog(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningCatalog> {
  return apiFetch<LearningCatalog>(API_ENDPOINTS.learningCourses, { accessToken, language, cache: "no-store" });
}

export async function fetchLearningMyModules(
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningMyModules> {
  return apiFetch<LearningMyModules>(API_ENDPOINTS.learningMy, { accessToken, language, cache: "no-store" });
}

export async function fetchLearningCourse(
  courseSlug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningCourseDetail> {
  return apiFetch<LearningCourseDetail>(apiPath.learningCourse(courseSlug), {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function fetchLearningLesson(
  courseSlug: string,
  lessonSlug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningLessonDetail> {
  return apiFetch<LearningLessonDetail>(apiPath.learningLesson(courseSlug, lessonSlug), {
    accessToken,
    language,
    cache: "no-store",
  });
}

export async function locateLearningLessonBySlug(
  lessonSlug: string,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<{ course_slug: string; lesson_slug: string; href: string } | null> {
  return apiFetch<{ course_slug: string; lesson_slug: string; href: string } | null>(
    apiPath.learningLocateLessonBySlug(lessonSlug),
    {
      accessToken,
      language,
      cache: "no-store",
    },
  );
}

export async function submitLearningStep(
  courseSlug: string,
  lessonSlug: string,
  stepSlug: string,
  answer: Record<string, unknown> | null,
  accessToken?: string | null,
  language?: Language | string | null,
): Promise<LearningStepSubmitResponse> {
  return apiFetch<LearningStepSubmitResponse>(apiPath.learningStepSubmit(courseSlug, lessonSlug, stepSlug), {
    method: "POST",
    body: JSON.stringify({ answer }),
    headers: {
      "Content-Type": "application/json",
    },
    accessToken,
    language,
    cache: "no-store",
  });
}
