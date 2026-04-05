import { API_ENDPOINTS, apiPath } from "../constants/api";
import type {
  LearningCourseDetail,
  LearningMyModules,
  LearningStepSubmitResponse,
  LessonCompletionResult,
} from "../types";
import { authFetch, jsonInit } from "./transport";

export async function completeLesson(slug: string): Promise<LessonCompletionResult> {
  return authFetch<LessonCompletionResult>(apiPath.lessonCompleteBySlug(slug), {
    method: "POST",
  });
}

export async function fetchLearningMyModules(): Promise<LearningMyModules> {
  return authFetch<LearningMyModules>(API_ENDPOINTS.learningMy);
}

export async function fetchLearningCourse(courseSlug: string): Promise<LearningCourseDetail> {
  return authFetch<LearningCourseDetail>(apiPath.learningCourse(courseSlug));
}

export async function submitLearningStep(
  courseSlug: string,
  lessonSlug: string,
  stepSlug: string,
  answer: Record<string, unknown> | null,
): Promise<LearningStepSubmitResponse> {
  return authFetch<LearningStepSubmitResponse>(
    apiPath.learningStepSubmit(courseSlug, lessonSlug, stepSlug),
    jsonInit("POST", { answer }),
  );
}
