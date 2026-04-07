import Link from "next/link";

import { LearningLessonRuntime } from "@/components/learning/LearningLessonRuntime";
import { T } from "@/components/i18n/T";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";

import type { LearningLessonStepPageData } from "./learning-step-page-data";

type LearningLessonStepViewProps = {
  language: Language;
  data: LearningLessonStepPageData;
};

export function LearningLessonStepView({ language, data }: LearningLessonStepViewProps) {
  const { course, step, canSubmit } = data;

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
        course={course}
        lesson={data.lesson}
        canSubmit={canSubmit}
        activeStepSlug={step.slug}
      />
    </article>
  );
}
