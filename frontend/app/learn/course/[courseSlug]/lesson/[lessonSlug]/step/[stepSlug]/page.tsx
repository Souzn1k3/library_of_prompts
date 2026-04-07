import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ApiRequestError } from "@/lib/api";
import { appRoute } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { LearningLessonStepView } from "./LearningLessonStepView";
import { loadLearningLessonStepPageData } from "./learning-step-page-data";

type Props = {
  params: Promise<{ courseSlug: string; lessonSlug: string; stepSlug: string }>;
};

export const revalidate = 0;

function buildStepMetadataFallback(
  courseSlug: string,
  lessonSlug: string,
  stepSlug: string,
  language: Language,
): Metadata {
  return buildPageMetadata({
    title: getTranslation(language, "learn.metadataFallbackTitle"),
    description: getTranslation(language, "meta.learnDescription"),
    path: appRoute.learnCourseLessonStep(courseSlug, lessonSlug, stepSlug),
    type: "article",
  });
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { courseSlug, lessonSlug, stepSlug } = await props.params;
  const language = await getServerLanguage();
  return buildStepMetadataFallback(courseSlug, lessonSlug, stepSlug, language);
}

export default async function LearningLessonStepPage(props: Props) {
  const { courseSlug, lessonSlug, stepSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const data = await loadLearningLessonStepPageData({
      courseSlug,
      lessonSlug,
      stepSlug,
      accessToken,
      language,
    });

    if (!data) {
      notFound();
    }

    return <LearningLessonStepView language={language} data={data} />;
  } catch (error) {
    if (error instanceof ApiRequestError && (error.status === 404 || error.status === 409)) {
      notFound();
    }

    return (
      <div className="pv-page-sm">
        <div className="pv-alert pv-alert-warning">
          {getTranslation(language, "learn.lessonLoadFailed")}
        </div>
      </div>
    );
  }
}
