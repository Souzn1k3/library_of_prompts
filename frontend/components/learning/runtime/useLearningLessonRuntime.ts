"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { submitLearningStep } from "@/lib/client-api";
import { appRoute } from "@/lib/constants/routes";
import type { EconomyAction, LearningLessonDetail, LearningStepSubmitResponse } from "@/lib/types";

import {
  buildInitialChoiceAnswers,
  buildInitialTextAnswers,
  buildSubmissionAnswer,
  extractErrorMessage,
  recomputeStepUnlocks,
  type StepChoiceAnswers,
} from "@/components/learning/runtime/helpers";
import type { LearningTranslation, StepState } from "@/components/learning/runtime/types";

type UseLearningLessonRuntimeArgs = {
  lesson: LearningLessonDetail;
  canSubmit: boolean;
  activeStepSlugProp: string;
  t: LearningTranslation;
};

type RuntimeStatusTone = "success" | "warning";

function buildInitialActiveStepSlug(lesson: LearningLessonDetail, activeStepSlugProp: string): string {
  return activeStepSlugProp || lesson.current_step_slug || lesson.steps[0]?.slug || "";
}

export function useLearningLessonRuntime({
  lesson,
  canSubmit,
  activeStepSlugProp,
  t,
}: UseLearningLessonRuntimeArgs) {
  const [steps, setSteps] = useState<StepState[]>(recomputeStepUnlocks(lesson.steps));
  const [activeStepSlug, setActiveStepSlug] = useState<string>(
    buildInitialActiveStepSlug(lesson, activeStepSlugProp),
  );
  const [lessonProgressPercent, setLessonProgressPercent] = useState<number>(lesson.progress_percent);
  const [courseProgressPercent, setCourseProgressPercent] = useState<number>(lesson.course_progress_percent);
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>(buildInitialTextAnswers(lesson.steps));
  const [choiceAnswers, setChoiceAnswers] = useState<StepChoiceAnswers>(buildInitialChoiceAnswers(lesson.steps));
  const [submittingStepSlug, setSubmittingStepSlug] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<RuntimeStatusTone | null>(null);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [weakAreas, setWeakAreas] = useState<LearningStepSubmitResponse["weak_areas"]>([]);
  const submittingStepRef = useRef<string | null>(null);

  useEffect(() => {
    if (activeStepSlugProp) {
      setActiveStepSlug(activeStepSlugProp);
    }
  }, [activeStepSlugProp]);

  useEffect(() => {
    setSteps(recomputeStepUnlocks(lesson.steps));
    setActiveStepSlug(buildInitialActiveStepSlug(lesson, activeStepSlugProp));
    setLessonProgressPercent(lesson.progress_percent);
    setCourseProgressPercent(lesson.course_progress_percent);
    setTextAnswers(buildInitialTextAnswers(lesson.steps));
    setChoiceAnswers(buildInitialChoiceAnswers(lesson.steps));
    setSubmittingStepSlug(null);
    setSubmitError(null);
    setStatusMessage(null);
    setStatusTone(null);
    setEconomy(null);
    setWeakAreas([]);
    submittingStepRef.current = null;
  }, [activeStepSlugProp, lesson]);

  const activeStepIndex = useMemo(() => {
    const index = steps.findIndex((step) => step.slug === activeStepSlug);
    return index >= 0 ? index : 0;
  }, [activeStepSlug, steps]);

  const activeStep = steps[activeStepIndex] ?? null;
  const previousStep = activeStepIndex > 0 ? steps[activeStepIndex - 1] : null;
  const nextStep = activeStepIndex < steps.length - 1 ? steps[activeStepIndex + 1] : null;
  const completedStepsCount = useMemo(() => steps.filter((step) => step.completed).length, [steps]);

  const stepHref = useCallback(
    (stepSlug: string) => appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, stepSlug),
    [lesson.course_slug, lesson.lesson_slug],
  );

  const setTextAnswer = useCallback((stepSlug: string, value: string) => {
    setTextAnswers((prev) => ({ ...prev, [stepSlug]: value }));
  }, []);

  const setChoiceAnswer = useCallback((stepSlug: string, questionId: string, choiceId: string) => {
    setChoiceAnswers((prev) => ({
      ...prev,
      [stepSlug]: {
        ...(prev[stepSlug] ?? {}),
        [questionId]: choiceId,
      },
    }));
  }, []);

  const handleSubmit = useCallback(
    async (step: StepState) => {
      if (!canSubmit) {
        setSubmitError(t("learn.signInToSubmit"));
        return;
      }
      if (!step.unlocked) {
        setSubmitError(t("learn.stepLockedLocal"));
        return;
      }
      if (submittingStepRef.current === step.slug) {
        return;
      }

      submittingStepRef.current = step.slug;
      setSubmittingStepSlug(step.slug);
      setSubmitError(null);
      setStatusMessage(null);
      setStatusTone(null);

      try {
        const result = await submitLearningStep(
          lesson.course_slug,
          lesson.lesson_slug,
          step.slug,
          buildSubmissionAnswer(step, choiceAnswers, textAnswers),
        );

        setSteps((prev) =>
          recomputeStepUnlocks(
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
          ),
        );

        setLessonProgressPercent(result.lesson_progress_percent);
        setCourseProgressPercent(result.course_progress_percent);
        setEconomy(result.economy ?? null);
        setWeakAreas(result.weak_areas ?? []);

        if (result.course_completed) {
          setStatusTone("success");
          setStatusMessage(
            `${t("learn.courseCompleted")} ${result.awarded_badge ? `(${result.awarded_badge})` : ""}`.trim(),
          );
        } else if (result.lesson_completed) {
          setStatusTone("success");
          setStatusMessage(t("learn.lessonCompleted"));
        } else {
          setStatusTone(result.passed ? "success" : "warning");
          setStatusMessage(result.passed ? t("learn.stepPassed") : t("learn.stepNeedsRevision"));
        }
      } catch (error) {
        setSubmitError(extractErrorMessage(error, t("learn.submitStepFallbackError")));
      } finally {
        submittingStepRef.current = null;
        setSubmittingStepSlug(null);
      }
    },
    [canSubmit, choiceAnswers, lesson.course_slug, lesson.lesson_slug, t, textAnswers],
  );

  return {
    steps,
    activeStepIndex,
    activeStep,
    previousStep,
    nextStep,
    completedStepsCount,
    lessonProgressPercent,
    courseProgressPercent,
    textAnswers,
    choiceAnswers,
    submittingStepSlug,
    submitError,
    statusMessage,
    statusTone,
    economy,
    weakAreas,
    stepHref,
    setTextAnswer,
    setChoiceAnswer,
    handleSubmit,
  };
}
