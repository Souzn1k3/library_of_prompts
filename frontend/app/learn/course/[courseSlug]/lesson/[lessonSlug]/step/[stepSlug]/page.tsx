import type { Metadata } from "next";
import Link from "next/link";
import { cache } from "react";
import { notFound } from "next/navigation";

import { LearningLessonRuntime } from "@/components/learning/LearningLessonRuntime";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { ApiRequestError, fetchLearningCourse, fetchLearningLesson } from "@/lib/api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatTranslation, getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = {
  params: Promise<{ courseSlug: string; lessonSlug: string; stepSlug: string }>;
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
  const { courseSlug, lessonSlug, stepSlug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();

  try {
    const lesson = await getLessonCached(courseSlug, lessonSlug, accessToken, language);
    const step = lesson.steps.find((item) => item.slug === stepSlug);
    const title = step ? `${lesson.title} · ${step.title}` : lesson.title;
    const description = step?.task ?? lesson.summary;

    return buildPageMetadata({
      title,
      description,
      path: appRoute.learnCourseLessonStep(courseSlug, lessonSlug, stepSlug),
      type: "article",
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "learn.metadataFallbackTitle"),
      description: getTranslation(language, "meta.learnDescription"),
      path: appRoute.learnCourseLessonStep(courseSlug, lessonSlug, stepSlug),
      type: "article",
    });
  }
}

export default async function LearningLessonStepPage(props: Props) {
  const { courseSlug, lessonSlug, stepSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const [lesson, course] = await Promise.all([
      getLessonCached(courseSlug, lessonSlug, accessToken, language),
      fetchLearningCourse(courseSlug, accessToken, language),
    ]);

    const stepIndex = lesson.steps.findIndex((step) => step.slug === stepSlug);
    if (stepIndex < 0) {
      notFound();
    }

    const step = lesson.steps[stepIndex];
    const previousStep = stepIndex > 0 ? lesson.steps[stepIndex - 1] : null;
    const nextStep = stepIndex < lesson.steps.length - 1 ? lesson.steps[stepIndex + 1] : null;
    const stepPositionLabel = formatTranslation(language, "learn.stepPosition", {
      current: stepIndex + 1,
      total: lesson.steps.length,
    });
    const stepKindLabel = getTranslation(language, `learn.stepKind.${step.kind}`);
    const stepMinutesLabel = formatTranslation(language, "learn.stepMinutesLabel", {
      count: step.estimated_minutes,
    });
    const stepHint = `${stepPositionLabel} · ${stepKindLabel} · ${stepMinutesLabel}`;

    return (
      <article className="pv-page">
        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
            { label: getTranslation(language, "nav.learn"), href: APP_ROUTES.learn },
            { label: course.title, href: appRoute.learnCourse(courseSlug) },
            { label: lesson.title, href: appRoute.learnCourseLesson(courseSlug, lessonSlug) },
            { label: step.title },
          ]}
          eyebrow={<T k="learn.lesson" />}
          title={lesson.title}
          description={lesson.summary}
          hint={stepHint}
          actions={
            <>
              <Link href={lesson.return_to_course_href} className="pv-button-secondary">
                <T k="learn.returnToCourse" />
              </Link>
              {nextStep ? (
                <Link
                  href={appRoute.learnCourseLessonStep(courseSlug, lessonSlug, nextStep.slug)}
                  className="pv-button-primary"
                >
                  <T k="learn.nextStepCta" />
                </Link>
              ) : lesson.next_lesson_href ? (
                <Link href={lesson.next_lesson_href} className="pv-button-primary">
                  <T k="learn.nextLessonCta" />
                </Link>
              ) : (
                <Link href={APP_ROUTES.learnMy} className="pv-button-primary">
                  <T k="learn.myModules" />
                </Link>
              )}
            </>
          }
        />

        {!accessToken ? (
          <section className="pv-alert pv-alert-warning">
            <p className="font-medium">{getTranslation(language, "learn.signInToSubmit")}</p>
            <div className="mt-3 flex flex-wrap gap-3">
              <Link href={APP_ROUTES.login} className="pv-button-secondary !w-auto">
                <T k="nav.login" />
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-primary !w-auto">
                <T k="nav.signup" />
              </Link>
            </div>
          </section>
        ) : null}

        <LearningLessonRuntime
          lesson={lesson}
          canSubmit={Boolean(accessToken)}
          activeStepSlug={stepSlug}
        />

        <section className="pv-panel px-6 py-5 sm:px-7">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link href={lesson.return_to_course_href} className="pv-inline-link">
              <T k="learn.returnToCourse" />
              <span aria-hidden="true">↗</span>
            </Link>

            <div className="flex flex-wrap items-center gap-3">
              {previousStep ? (
                <Link
                  href={appRoute.learnCourseLessonStep(courseSlug, lessonSlug, previousStep.slug)}
                  className="pv-button-secondary !w-auto"
                >
                  <T k="learn.previousStep" />
                </Link>
              ) : lesson.previous_lesson_href ? (
                <Link href={lesson.previous_lesson_href} className="pv-button-secondary !w-auto">
                  <T k="learn.previousLesson" />
                </Link>
              ) : null}

              {nextStep ? (
                <Link
                  href={appRoute.learnCourseLessonStep(courseSlug, lessonSlug, nextStep.slug)}
                  className="pv-button-primary !w-auto"
                >
                  <T k="learn.nextStep" />
                </Link>
              ) : lesson.next_lesson_href ? (
                <Link href={lesson.next_lesson_href} className="pv-button-primary !w-auto">
                  <T k="learn.nextLesson" />
                </Link>
              ) : (
                <Link href={lesson.return_to_course_href} className="pv-button-primary !w-auto">
                  <T k="learn.courseCompleteState" />
                </Link>
              )}
            </div>
          </div>
        </section>
      </article>
    );
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
