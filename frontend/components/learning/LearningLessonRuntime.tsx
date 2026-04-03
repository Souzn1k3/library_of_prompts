"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { submitLearningStep } from "@/lib/client-api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import type {
  EconomyAction,
  LearningLessonDetail,
  LearningLessonStep,
  LearningStepFeedback,
  LearningStepSubmitResponse,
} from "@/lib/types";

type LearningLessonRuntimeProps = {
  lesson: LearningLessonDetail;
  canSubmit: boolean;
  activeStepSlug: string;
};

type StepState = LearningLessonStep & {
  feedback?: LearningStepFeedback | null;
};

function defaultTextAnswer(step: LearningLessonStep): string {
  return step.submission_type === "text" ? "" : "";
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return "Could not submit this step. Please try again.";
}

function suggestedTemplate(
  step: LearningLessonStep,
  t: (key: string, params?: Record<string, string | number | null | undefined>) => string,
): string | null {
  if (step.placeholder && step.placeholder.trim().length > 0) {
    return step.placeholder.trim();
  }
  if (step.kind === "guided_practice") {
    return t("learn.templateGuided");
  }
  if (step.kind === "applied_exercise") {
    return t("learn.templateApplied");
  }
  if (step.kind === "reflection") {
    return t("learn.templateReflection");
  }
  return null;
}

export function LearningLessonRuntime({
  lesson,
  canSubmit,
  activeStepSlug: activeStepSlugProp,
}: LearningLessonRuntimeProps) {
  const { t } = useI18n();
  const router = useRouter();

  const [steps, setSteps] = useState<StepState[]>(lesson.steps);
  const [activeStepSlug, setActiveStepSlug] = useState<string>(
    activeStepSlugProp || lesson.current_step_slug || lesson.steps[0]?.slug || "",
  );
  const [lessonProgressPercent, setLessonProgressPercent] = useState<number>(lesson.progress_percent);
  const [courseProgressPercent, setCourseProgressPercent] = useState<number>(lesson.course_progress_percent);
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>(
    Object.fromEntries(lesson.steps.map((step) => [step.slug, defaultTextAnswer(step)])),
  );
  const [choiceAnswers, setChoiceAnswers] = useState<Record<string, string>>({});
  const [submittingStepSlug, setSubmittingStepSlug] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [economy, setEconomy] = useState<EconomyAction | null>(null);
  const [weakAreas, setWeakAreas] = useState(
    lesson.steps.length ? ([] as LearningStepSubmitResponse["weak_areas"]) : [],
  );

  useEffect(() => {
    if (activeStepSlugProp) {
      setActiveStepSlug(activeStepSlugProp);
    }
  }, [activeStepSlugProp]);

  const activeStepIndex = useMemo(() => {
    const index = steps.findIndex((step) => step.slug === activeStepSlug);
    return index >= 0 ? index : 0;
  }, [activeStepSlug, steps]);

  const activeStep = steps[activeStepIndex] ?? null;
  const previousStep = activeStepIndex > 0 ? steps[activeStepIndex - 1] : null;
  const nextStep = activeStepIndex < steps.length - 1 ? steps[activeStepIndex + 1] : null;

  function stepHref(stepSlug: string): string {
    return appRoute.learnCourseLessonStep(lesson.course_slug, lesson.lesson_slug, stepSlug);
  }

  async function handleSubmit(step: StepState) {
    if (!canSubmit) {
      setSubmitError(t("learn.signInToSubmit"));
      return;
    }

    const answer =
      step.submission_type === "choice"
        ? { choice_id: choiceAnswers[step.slug] ?? "" }
        : step.submission_type === "text"
          ? { text: textAnswers[step.slug] ?? "" }
          : null;

    setSubmittingStepSlug(step.slug);
    setSubmitError(null);
    setStatusMessage(null);

    try {
      const result = await submitLearningStep(
        lesson.course_slug,
        lesson.lesson_slug,
        step.slug,
        answer,
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
        router.push(stepHref(result.next_step_slug));
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
  }

  if (!activeStep) {
    return (
      <section className="pv-alert pv-alert-warning">
        {t("learn.lessonLoadFailed")}
      </section>
    );
  }

  const isSubmitting = submittingStepSlug === activeStep.slug;

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start">
      <aside className="pv-panel px-5 py-5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold text-zinc-900">{t("learn.lessonList")}</p>
          <span className="pv-chip-brand">{courseProgressPercent}%</span>
        </div>

        <div
          className="mt-3 pv-progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={courseProgressPercent}
        >
          <div className="pv-progress-fill" style={{ width: `${courseProgressPercent}%` }} />
        </div>

        <ol className="mt-4 grid gap-2">
          {lesson.lesson_list.map((item) => (
            <li key={item.slug}>
              <Link
                href={item.continue_href}
                className={`block rounded-[1rem] border px-3 py-2 text-sm transition ${
                  item.slug === lesson.lesson_slug
                    ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-900"
                    : item.unlocked
                      ? "border-[var(--pv-border)] bg-white/90 text-zinc-700 hover:border-zinc-300"
                      : "pointer-events-none border-[var(--pv-border)] bg-zinc-100/60 text-zinc-400"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate">
                    {item.position}. {item.title}
                  </span>
                  <span className="text-xs">{item.progress_percent}%</span>
                </div>
              </Link>
            </li>
          ))}
        </ol>
      </aside>

      <section className="space-y-4">
        <div className="pv-panel px-6 py-5 sm:px-7">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm font-medium text-zinc-900">
              {t("learn.lessonProgress")}: {lessonProgressPercent}%
            </p>
            <p className="text-sm text-zinc-600">
              {t("learn.lessonEstimated")}: {lesson.estimated_minutes}m
            </p>
          </div>
          <div
            className="mt-3 pv-progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={lessonProgressPercent}
          >
            <div className="pv-progress-fill" style={{ width: `${lessonProgressPercent}%` }} />
          </div>
        </div>

        {statusMessage ? <div className="pv-alert pv-alert-success">{statusMessage}</div> : null}
        {submitError ? <div className="pv-alert pv-alert-warning">{submitError}</div> : null}
        <EconomyActionBanner summary={economy} ctaHref={APP_ROUTES.store} />

        <nav className="pv-panel px-4 py-4 sm:px-5">
          <ol className="flex flex-wrap gap-2">
            {steps.map((step, index) => (
              <li key={step.slug}>
                <Link
                  href={stepHref(step.slug)}
                  className={`inline-flex items-center rounded-full border px-3 py-2 text-sm font-medium transition ${
                    index === activeStepIndex
                      ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-950"
                      : "border-[var(--pv-border)] bg-white/90 text-zinc-700 hover:border-zinc-300"
                  }`}
                >
                  {index + 1}. {t(`learn.stepKind.${step.kind}`)}
                </Link>
              </li>
            ))}
          </ol>
        </nav>

        <article className="pv-panel px-6 py-6 sm:px-7 ring-1 ring-[var(--pv-brand)]/40">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="pv-kicker">{t(`learn.stepKind.${activeStep.kind}`)}</p>
              <p className="mt-1 text-xs text-zinc-500">
                {t("learn.stepPosition", { current: activeStepIndex + 1, total: steps.length })}
              </p>
              <h3 className="mt-2 text-xl font-bold tracking-[-0.04em] text-zinc-950">
                {activeStep.title}
              </h3>
            </div>
            <span className="pv-chip-brand">
              {t("learn.stepMinutesLabel", { count: activeStep.estimated_minutes })}
            </span>
          </div>

          {activeStep.content.length > 0 ? (
            <div className="mt-4 space-y-3 text-sm leading-relaxed text-zinc-700">
              {activeStep.content.map((line, lineIdx) => (
                <p key={`${activeStep.slug}-content-${lineIdx}`}>{line}</p>
              ))}
            </div>
          ) : null}

          {activeStep.task ? (
            <div className="mt-4 rounded-[1.1rem] border border-[var(--pv-border)] bg-white/80 p-4 text-sm text-zinc-700">
              {activeStep.task}
            </div>
          ) : null}

          {activeStep.submission_type === "choice" ? (
            <fieldset className="mt-4 grid gap-2">
              {activeStep.question ? (
                <legend className="text-sm font-medium text-zinc-900">{activeStep.question}</legend>
              ) : null}
              {activeStep.choices.map((choice) => (
                <label
                  key={choice.id}
                  className="flex cursor-pointer items-start gap-2 rounded-[0.9rem] border border-[var(--pv-border)] bg-white/80 px-3 py-2 text-sm text-zinc-700"
                >
                  <input
                    type="radio"
                    name={`choice-${activeStep.slug}`}
                    className="mt-[0.2rem]"
                    checked={(choiceAnswers[activeStep.slug] ?? "") === choice.id}
                    onChange={() =>
                      setChoiceAnswers((prev) => ({ ...prev, [activeStep.slug]: choice.id }))
                    }
                    disabled={!canSubmit || isSubmitting}
                  />
                  <span>{choice.text}</span>
                </label>
              ))}
            </fieldset>
          ) : null}

          {activeStep.submission_type === "text" ? (
            <div className="mt-4 space-y-3">
              {suggestedTemplate(activeStep, t) ? (
                <details className="rounded-[1rem] border border-[var(--pv-border)] bg-white/80 px-4 py-3">
                  <summary className="cursor-pointer select-none text-sm font-semibold text-zinc-900">
                    {t("learn.readyPrompt")}
                  </summary>
                  <p className="mt-2 text-sm text-zinc-600">{t("learn.readyPromptHint")}</p>
                  <pre className="mt-3 overflow-x-auto rounded-[0.9rem] border border-[var(--pv-border)] bg-zinc-50 px-3 py-3 text-xs leading-relaxed text-zinc-800">
                    {suggestedTemplate(activeStep, t)}
                  </pre>
                </details>
              ) : null}
              <p className="text-xs text-zinc-500">{t("learn.answerFormatHint")}</p>
              {activeStep.kind === "reflection" ? (
                <p className="rounded-[0.9rem] border border-[var(--pv-border)] bg-zinc-50/80 px-3 py-2 text-xs text-zinc-600">
                  {t("learn.reflectionHint")}
                </p>
              ) : null}
              <textarea
                value={textAnswers[activeStep.slug] ?? ""}
                onChange={(event) =>
                  setTextAnswers((prev) => ({ ...prev, [activeStep.slug]: event.target.value }))
                }
                placeholder={activeStep.placeholder ?? ""}
                disabled={!canSubmit || isSubmitting}
                className="min-h-[180px] w-full rounded-[1rem] border border-[var(--pv-border)] bg-white/90 px-3 py-3 text-sm text-zinc-900 outline-none transition focus:border-zinc-400"
              />
            </div>
          ) : null}

          {activeStep.feedback ? (
            <div className="mt-4 rounded-[1rem] border border-emerald-200 bg-emerald-50/70 p-4 text-sm text-emerald-950">
              <p className="font-semibold">
                {activeStep.feedback.verdict} · {activeStep.feedback.score}/{activeStep.feedback.pass_score}
              </p>
              {activeStep.feedback.strengths.length > 0 ? (
                <ul className="mt-2 grid gap-1 text-emerald-900">
                  {activeStep.feedback.strengths.map((item) => (
                    <li key={`${activeStep.slug}-strength-${item}`}>• {item}</li>
                  ))}
                </ul>
              ) : null}
              {activeStep.feedback.improvements.length > 0 ? (
                <ul className="mt-2 grid gap-1 text-amber-900">
                  {activeStep.feedback.improvements.map((item) => (
                    <li key={`${activeStep.slug}-improvement-${item}`}>• {item}</li>
                  ))}
                </ul>
              ) : null}
              {activeStep.feedback.revisit.length > 0 ? (
                <ul className="mt-2 grid gap-1 text-zinc-800">
                  {activeStep.feedback.revisit.map((item) => (
                    <li key={`${activeStep.slug}-revisit-${item}`}>• {item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            {previousStep ? (
              <Link href={stepHref(previousStep.slug)} className="pv-button-secondary !w-auto">
                {t("learn.previousStep")}
              </Link>
            ) : null}

            <button
              type="button"
              onClick={() => void handleSubmit(activeStep)}
              disabled={isSubmitting || !canSubmit}
              className="pv-button-primary !w-auto disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting
                ? t("learn.checking")
                : activeStep.completed
                  ? t("learn.retryStep")
                  : t("learn.checkStep")}
            </button>

            {nextStep ? (
              <Link href={stepHref(nextStep.slug)} className="pv-button-secondary !w-auto">
                {t("learn.nextStep")}
              </Link>
            ) : null}

            <span className="text-xs text-zinc-500">
              {t("learn.attempts")}: {activeStep.attempts} · {t("learn.attemptsHint")}
            </span>
          </div>
        </article>

        {weakAreas.length > 0 ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <p className="text-sm font-semibold text-zinc-900">{t("learn.recommendedFocus")}</p>
            <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
              {weakAreas.map((item) => (
                <li key={`${item.tag}-${item.lesson_slug ?? "none"}`}>• {item.recommendation}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </section>
    </div>
  );
}
