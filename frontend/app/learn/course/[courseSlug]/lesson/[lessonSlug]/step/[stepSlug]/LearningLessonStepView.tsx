import Link from "next/link";

import { LearningLessonRuntime } from "@/components/learning/LearningLessonRuntime";
import { T } from "@/components/i18n/T";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";

import type { LearningLessonStepPageData } from "./learning-step-page-data";

type LearningLessonStepViewProps = {
  language: Language;
  data: LearningLessonStepPageData;
};

export function LearningLessonStepView({ language, data }: LearningLessonStepViewProps) {
  const { lesson, course, step, previousStep, nextStep, canSubmit } = data;

  return (
    <article className="pv-page">
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
        courseTitle={course.title}
        canSubmit={canSubmit}
        activeStepSlug={step.slug}
      />

      <section className="pv-panel px-6 py-5 sm:px-7">
        <div className="flex flex-wrap items-center justify-end gap-3">
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
      </section>
    </article>
  );
}
