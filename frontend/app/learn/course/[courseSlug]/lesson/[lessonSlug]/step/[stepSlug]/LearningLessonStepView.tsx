import Link from "next/link";

import { LearningLessonRuntime } from "@/components/learning/LearningLessonRuntime";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";

import type { LearningLessonStepPageData } from "./learning-step-page-data";

type LearningLessonStepViewProps = {
  language: Language;
  data: LearningLessonStepPageData;
};

export function LearningLessonStepView({ language, data }: LearningLessonStepViewProps) {
  const { lesson, course, step, previousStep, nextStep, stepIndex, canSubmit } = data;
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
          { label: course.title, href: appRoute.learnCourse(lesson.course_slug) },
          { label: lesson.title, href: appRoute.learnCourseLesson(lesson.course_slug, lesson.lesson_slug) },
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
                href={appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, nextStep.slug)}
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

      {!canSubmit ? (
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
        canSubmit={canSubmit}
        activeStepSlug={step.slug}
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
                href={appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, previousStep.slug)}
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
                href={appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, nextStep.slug)}
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
}
