import type { Metadata } from "next";
import { cache } from "react";
import { notFound, redirect } from "next/navigation";

import { ApiRequestError, fetchLearningLesson } from "@/lib/api";
import { appRoute } from "@/lib/constants/routes";
import { getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = {
  params: Promise<{ courseSlug: string; lessonSlug: string }>;
};

const getLessonCached = cache(
  async (
    courseSlug: string,
    lessonSlug: string,
    accessToken: string | null | undefined,
    language: string,
  ) => fetchLearningLesson(courseSlug, lessonSlug, accessToken, language),
);

export const revalidate = 0;

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { courseSlug, lessonSlug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();

  try {
    const lesson = await getLessonCached(courseSlug, lessonSlug, accessToken, language);
    return buildPageMetadata({
      title: lesson.title,
      description: lesson.summary,
      path: appRoute.learnCourseLesson(courseSlug, lessonSlug),
      type: "article",
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "learn.metadataFallbackTitle"),
      description: getTranslation(language, "meta.learnDescription"),
      path: appRoute.learnCourseLesson(courseSlug, lessonSlug),
      type: "article",
    });
  }
}

export default async function LearningLessonPage(props: Props) {
  const { courseSlug, lessonSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  let lesson: Awaited<ReturnType<typeof getLessonCached>>;
  try {
    lesson = await getLessonCached(courseSlug, lessonSlug, accessToken, language);
  } catch (error) {
    if (error instanceof ApiRequestError && (error.status === 404 || error.status === 409)) {
      notFound();
    }

    return <div className="pv-page-sm"><div className="pv-alert pv-alert-warning">{getTranslation(language, "learn.lessonLoadFailed")}</div></div>;
  }

  const stepSlug = lesson.current_step_slug ?? lesson.steps[0]?.slug;
  if (!stepSlug) {
    notFound();
  }

  redirect(appRoute.learnCourseLessonStep(courseSlug, lessonSlug, stepSlug));
}
