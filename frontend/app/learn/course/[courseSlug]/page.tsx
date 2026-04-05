import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ApiRequestError } from "@/lib/api";
import { appRoute } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { LearningCoursePageView } from "./LearningCoursePageView";
import { getLearningCourseCached, loadLearningCoursePageData } from "./learning-course-page-data";

type Props = { params: Promise<{ courseSlug: string }> };

export const revalidate = 0;

function buildLearningMetadataFallback(courseSlug: string, language: Language): Metadata {
  return buildPageMetadata({
    title: getTranslation(language, "meta.learnTitle"),
    description: getTranslation(language, "meta.learnDescription"),
    path: appRoute.learnCourse(courseSlug),
  });
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { courseSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const course = await getLearningCourseCached(courseSlug, accessToken, language);
    return buildPageMetadata({
      title: course.title,
      description: course.description,
      path: appRoute.learnCourse(courseSlug),
    });
  } catch {
    return buildLearningMetadataFallback(courseSlug, language);
  }
}

export default async function LearningCoursePage(props: Props) {
  const { courseSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const data = await loadLearningCoursePageData({ courseSlug, accessToken, language });
    return <LearningCoursePageView language={language} data={data} />;
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 404) {
      notFound();
    }
    return <div className="pv-page-sm"><div className="pv-alert pv-alert-warning">{getTranslation(language, "learn.lessonLoadFailed")}</div></div>;
  }
}
