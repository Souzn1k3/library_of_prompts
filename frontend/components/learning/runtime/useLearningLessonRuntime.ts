"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { submitLearningStep } from "@/lib/client-api";
import { appRoute } from "@/lib/constants/routes";
import type { EconomyAction, LearningLessonDetail, LearningStepSubmitResponse } from "@/lib/types";

import {
  buildInitialTextAnswers,
  buildSubmissionAnswer,
  extractErrorMessage,
} from "@/components/learning/runtime/helpers";
import type { LearningTranslation, StepState } from "@/components/learning/runtime/types";

type UseLearningLessonRuntimeArgs = {
  lesson: LearningLessonDetail;
  canSubmit: boolean;
  activeStepSlugProp: string;
  t: LearningTranslation;
  onNavigate: (href: string) => void;
};

function buildInitialActiveStepSlug(lesson: LearningLessonDetail, activeStepSlugProp: string): string {
  return activeStepSlugProp || lesson.current_step_slug || lesson.steps[0]?.slug || "";
}

export function useLearningLessonRuntime({
  lesson,
  canSubmit,
  activeStepSlugProp,
  t,
  onNavigate,
}: UseLearningLessonRuntimeArgs) {
  const [steps, setSteps] = useState<StepState[]>(lesson.steps);
  const [activeStepSlug, setActiveStepSlug] = useState<string>(
    buildInitialActiveStepSlug(lesson, activeStepSlugProp),
  );
  const [lessonProgressPercent, setLessonProgressPercent] = useState<number>(lesson.progress_percent);
  const [courseProgressPercent, setCourseProgressPercent] = useState<number>(lesson.course_progress_percent);
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>(buildInitialTextAnswers(lesson.steps));
  const [choiceAnswers, setChoiceAnswers] = useState<Record<string, string>>({});
  const [submittingStepSlug, setSubmittingStepSlug] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [weakAreas, setWeakAreas] = useState<LearningStepSubmitResponse["weak_areas"]>([]);

  useEffect(() => {
    if (activeStepSlugProp) {
      setActiveStepSlug(activeStepSlugProp);
    }
  }, [activeStepSlugProp]);

  useEffect(() => {
    setSteps(lesson.steps);
    setActiveStepSlug(buildInitialActiveStepSlug(lesson, activeStepSlugProp));
    setLessonProgressPercent(lesson.progress_percent);
    setCourseProgressPercent(lesson.course_progress_percent);
    setTextAnswers(buildInitialTextAnswers(lesson.steps));
    setChoiceAnswers({});
    setSubmittingStepSlug(null);
    setSubmitError(null);
    setStatusMessage(null);
    setEconomy(null);
    setWeakAreas([]);
  }, [activeStepSlugProp, lesson]);

  const activeStepIndex = useMemo(() => {
    const index = steps.findIndex((step) => step.slug === activeStepSlug);
    return index >= 0 ? index : 0;
  }, [activeStepSlug, steps]);

  const activeStep = steps[activeStepIndex] ?? null;
  const previousStep = activeStepIndex > 0 ? steps[activeStepIndex - 1] : null;
  const nextStep = activeStepIndex < steps.length - 1 ? steps[activeStepIndex + 1] : null;

  const stepHref = useCallback(
    (stepSlug: string) => appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, stepSlug),
    [lesson.course_slug, lesson.lesson_slug],
  );

  const setTextAnswer = useCallback((stepSlug: string, value: string) => {
    setTextAnswers((prev) => ({ ...prev, [stepSlug]: value }));
  }, []);

  const setChoiceAnswer = useCallback((stepSlug: string, choiceId: string) => {
    setChoiceAnswers((prev) => ({ ...prev, [stepSlug]: choiceId }));
  }, []);

  const handleSubmit = useCallback(
    async (step: StepState) => {
      if (!canSubmit) {
        setSubmitError(t("learn.signInToSubmit"));
        return;
      }

      setSubmittingStepSlug(step.slug);
      setSubmitError(null);
      setStatusMessage(null);

      try {
        const result = await submitLearningStep(
          lesson.course_slug,
          lesson.lesson_slug,
          step.slug,
          buildSubmissionAnswer(step, choiceAnswers, textAnswers),
        );

        setSteps((prev) =>
          prev.map((item) =>
            item.slug === step.slug
              ? {
                  ...item,
                  completed: result.completed,
                  attempts: result.attempts,
                  last_score: result.score,
                  feedback: result.feedback,
                }
              : item,
          ),
        );

        setLessonProgressPercent(result.lesson_progress_percent);
        setCourseProgressPercent(result.course_progress_percent);
        setEconomy(result.economy ?? null);
        setWeakAreas(result.weak_areas ?? []);

        if (result.next_step_slug) {
          setActiveStepSlug(result.next_step_slug);
          onNavigate(stepHref(result.next_step_slug));
        }

        if (result.course_completed) {
          setStatusMessage(
            `${t("learn.courseCompleted")} ${result.awarded_badge ? `(${result.awarded_badge})` : ""}`.trim(),
          );
        } else if (result.lesson_completed) {
          setStatusMessage(t("learn.lessonCompleted"));
        } else {
          setStatusMessage(result.passed ? t("learn.stepPassed") : t("learn.stepNeedsRevision"));
        }
      } catch (error) {
        setSubmitError(extractErrorMessage(error));
      } finally {
        setSubmittingStepSlug(null);
      }
    },
    [canSubmit, choiceAnswers, lesson.course_slug, lesson.lesson_slug, onNavigate, stepHref, t, textAnswers],
  );

  return {
    steps,
    activeStepIndex,
    activeStep,
    previousStep,
    nextStep,
    lessonProgressPercent,
    courseProgressPercent,
    textAnswers,
    choiceAnswers,
    submittingStepSlug,
    submitError,
    statusMessage,
    economy,
    weakAreas,
    stepHref,
    setTextAnswer,
    setChoiceAnswer,
    handleSubmit,
  };
}
