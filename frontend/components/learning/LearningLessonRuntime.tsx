"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LearningStepArticle } from "@/components/learning/runtime/LearningStepArticle";
import { LessonOutlineSidebar } from "@/components/learning/runtime/LessonOutlineSidebar";
import { useLearningLessonRuntime } from "@/components/learning/runtime/useLearningLessonRuntime";
import { LearningWeakAreasPanel } from "@/components/learning/runtime/LearningWeakAreasPanel";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { LearningLessonDetail } from "@/lib/types";

type LearningLessonRuntimeProps = {
  lesson: LearningLessonDetail;
  courseTitle: string;
  canSubmit: boolean;
  activeStepSlug: string;
};

export function LearningLessonRuntime({
  lesson,
  courseTitle,
  canSubmit,
  activeStepSlug: activeStepSlugProp,
}: LearningLessonRuntimeProps) {
  const { t } = useI18n();
  const {
    steps,
    activeStepIndex,
    activeStep,
    previousStep,
    nextStep,
    completedStepsCount,
    courseProgressPercent,
    textAnswers,
    choiceAnswers,
    submittingStepSlug,
    submitError,
    economy,
    weakAreas,
    stepHref,
    setTextAnswer,
    setChoiceAnswer,
    handleSubmit,
  } = useLearningLessonRuntime({
    lesson,
    canSubmit,
    activeStepSlugProp,
    t,
  });

  if (!activeStep) {
    return (
      <section className="pv-alert pv-alert-warning">
        {t("learn.lessonLoadFailed")}
      </section>
    );
  }

  const isSubmitting = submittingStepSlug === activeStep.slug;
  const theoryStepSlug =
    [...steps.slice(0, activeStepIndex)].reverse().find((step) => step.kind === "theory")?.slug ??
    steps.find((step) => step.kind === "theory")?.slug ??
    null;

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start">
      <LessonOutlineSidebar
        lesson={lesson}
        courseTitle={courseTitle}
        returnToCourseHref={lesson.return_to_course_href}
        courseProgressPercent={courseProgressPercent}
        steps={steps}
        activeStepIndex={activeStepIndex}
        stepHref={stepHref}
      />

      <section className="space-y-4">
        {submitError ? <div className="pv-alert pv-alert-warning">{submitError}</div> : null}
        <LearningStepArticle
          activeStep={activeStep}
          activeStepIndex={activeStepIndex}
          stepsCount={steps.length}
          completedStepsCount={completedStepsCount}
          previousStep={previousStep}
          nextStep={nextStep}
          theoryStepSlug={theoryStepSlug}
          canSubmit={canSubmit}
          isSubmitting={isSubmitting}
          selectedChoiceId={choiceAnswers[activeStep.slug] ?? ""}
          textAnswer={textAnswers[activeStep.slug] ?? ""}
          stepHref={stepHref}
          onChoiceChange={(choiceId) => setChoiceAnswer(activeStep.slug, choiceId)}
          onTextChange={(value) => setTextAnswer(activeStep.slug, value)}
          onSubmitStep={() => void handleSubmit(activeStep)}
        />

        <EconomyActionBanner summary={economy} ctaHref={APP_ROUTES.store} />

        <LearningWeakAreasPanel weakAreas={weakAreas} />
      </section>
    </div>
  );
}
