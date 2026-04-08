import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiRequestError, locateLearningLessonBySlug } from "@/lib/api";
import { APP_ROUTES, appRoute, LEARNING_FOUNDATIONS_COURSE_SLUG } from "@/lib/constants/routes";
import { getTranslation } from "@/lib/i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { LearningLessonStepView } from "../course/[courseSlug]/lesson/[lessonSlug]/step/[stepSlug]/LearningLessonStepView";
import { loadLearningLessonStepPageData } from "../course/[courseSlug]/lesson/[lessonSlug]/step/[stepSlug]/learning-step-page-data";

type Props = { params: Promise<{ slug: string }> };

export const revalidate = 0;

export default async function LegacyLessonCompatibilityPage(props: Props) {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();

  try {
    const locate = await locateLearningLessonBySlug(slug, accessToken, language);
    if (locate) {
      const data = await loadLearningLessonStepPageData({
        courseSlug: locate.course_slug,
        lessonSlug: locate.lesson_slug,
        accessToken,
        language,
      });

      if (!data) {
        notFound();
      }

      return <LearningLessonStepView language={language} data={data} />;
    }
  } catch (error) {
    if (error instanceof ApiRequestError && (error.status === 404 || error.status === 409)) {
      notFound();
    }

    return (
      <div className="pv-page-sm">
        <div className="pv-alert pv-alert-warning">{getTranslation(language, "learn.lessonLoadFailed")}</div>
      </div>
    );
  }

  return (
    <div className="pv-page-sm space-y-4">
      <div className="pv-alert pv-alert-warning">{getTranslation(language, "learn.lessonLoadFailed")}</div>
      <div className="pv-action-bar pv-action-bar-start">
        <Link href={appRoute.learnCourse(LEARNING_FOUNDATIONS_COURSE_SLUG)} className="pv-button-primary !w-auto">
          {getTranslation(language, "home.startLearning")}
        </Link>
        <Link href={APP_ROUTES.learn} className="pv-inline-link">
          {getTranslation(language, "nav.learn")}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}
