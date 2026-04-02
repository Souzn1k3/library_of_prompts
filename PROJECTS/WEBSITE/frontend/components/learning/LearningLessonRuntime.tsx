"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { submitLearningStep } from "@/lib/client-api";
import { APP_ROUTES } from "@/lib/constants/routes";
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

function suggestedTemplate(step: LearningLessonStep, t: (key: string, params?: Record<string, string | number | null | undefined>) => string): string | null {
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

export function LearningLessonRuntime({ lesson, canSubmit }: LearningLessonRuntimeProps) {
  const { t } = useI18n();

  const [steps, setSteps] = useState<StepState[]>(lesson.steps);
  const [activeStepSlug, setActiveStepSlug] = useState<string | null>(
    lesson.current_step_slug ?? lesson.steps[0]?.slug ?? null,
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
  const [weakAreas, setWeakAreas] = useState(lesson.steps.length ? [] as LearningStepSubmitResponse["weak_areas"] : []);

  const activeStepIndex = useMemo(
    () => Math.max(0, steps.findIndex((step) => step.slug === activeStepSlug)),
    [activeStepSlug, steps],
  );

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
      const result = await submitLearningStep(lesson.course_slug, lesson.lesson_slug, step.slug, answer);

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

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start">
      <aside className="pv-panel px-5 py-5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold text-zinc-900">{t("learn.lessonList")}</p>
          <span className="pv-chip-brand">{courseProgressPercent}%</span>
        </div>

        <div className="mt-3 pv-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={courseProgressPercent}>
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
                  <span className="truncate">{item.position}. {item.title}</span>
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
          <div className="mt-3 pv-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={lessonProgressPercent}>
            <div className="pv-progress-fill" style={{ width: `${lessonProgressPercent}%` }} />
          </div>
        </div>

        {statusMessage ? <div className="pv-alert pv-alert-success">{statusMessage}</div> : null}
        {submitError ? <div className="pv-alert pv-alert-warning">{submitError}</div> : null}
        <EconomyActionBanner summary={economy} ctaHref={APP_ROUTES.store} />

        <div className="grid gap-4">
          {steps.map((step, index) => {
            const isActive = index === activeStepIndex || step.slug === activeStepSlug;
            const isSubmitting = submittingStepSlug === step.slug;

            return (
              <article
                key={step.slug}
                className={`pv-panel px-6 py-6 sm:px-7 ${isActive ? "ring-1 ring-[var(--pv-brand)]/40" : ""}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="pv-kicker">{t(`learn.stepKind.${step.kind}`)}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {t("learn.stepPosition", { current: index + 1, total: steps.length })}
                    </p>
                    <h3 className="mt-2 text-xl font-bold tracking-[-0.04em] text-zinc-950">{step.title}</h3>
                  </div>
                  <span className="pv-chip-brand">
                    {t("learn.stepMinutesLabel", { count: step.estimated_minutes })}
                  </span>
                </div>

                {step.content.length > 0 ? (
                  <div className="mt-4 space-y-3 text-sm leading-relaxed text-zinc-700">
                    {step.content.map((line, lineIdx) => (
                      <p key={`${step.slug}-content-${lineIdx}`}>{line}</p>
                    ))}
                  </div>
                ) : null}

                {step.task ? (
                  <div className="mt-4 rounded-[1.1rem] border border-[var(--pv-border)] bg-white/80 p-4 text-sm text-zinc-700">
                    {step.task}
                  </div>
                ) : null}

                {step.submission_type === "choice" ? (
                  <fieldset className="mt-4 grid gap-2">
                    {step.question ? <legend className="text-sm font-medium text-zinc-900">{step.question}</legend> : null}
                    {step.choices.map((choice) => (
                      <label
                        key={choice.id}
                        className="flex cursor-pointer items-start gap-2 rounded-[0.9rem] border border-[var(--pv-border)] bg-white/80 px-3 py-2 text-sm text-zinc-700"
                      >
                        <input
                          type="radio"
                          name={`choice-${step.slug}`}
                          className="mt-[0.2rem]"
                          checked={(choiceAnswers[step.slug] ?? "") === choice.id}
                          onChange={() => setChoiceAnswers((prev) => ({ ...prev, [step.slug]: choice.id }))}
                          disabled={!canSubmit || isSubmitting}
                        />
                        <span>{choice.text}</span>
                      </label>
                    ))}
                  </fieldset>
                ) : null}

                {step.submission_type === "text" ? (
                  <div className="mt-4 space-y-3">
                    {suggestedTemplate(step, t) ? (
                      <details className="rounded-[1rem] border border-[var(--pv-border)] bg-white/80 px-4 py-3">
                        <summary className="cursor-pointer select-none text-sm font-semibold text-zinc-900">
                          {t("learn.readyPrompt")}
                        </summary>
                        <p className="mt-2 text-sm text-zinc-600">{t("learn.readyPromptHint")}</p>
                        <pre className="mt-3 overflow-x-auto rounded-[0.9rem] border border-[var(--pv-border)] bg-zinc-50 px-3 py-3 text-xs leading-relaxed text-zinc-800">
                          {suggestedTemplate(step, t)}
                        </pre>
                      </details>
                    ) : null}
                    <p className="text-xs text-zinc-500">{t("learn.answerFormatHint")}</p>
                    {step.kind === "reflection" ? (
                      <p className="rounded-[0.9rem] border border-[var(--pv-border)] bg-zinc-50/80 px-3 py-2 text-xs text-zinc-600">
                        {t("learn.reflectionHint")}
                      </p>
                    ) : null}
                    <textarea
                      value={textAnswers[step.slug] ?? ""}
                      onChange={(event) => setTextAnswers((prev) => ({ ...prev, [step.slug]: event.target.value }))}
                      placeholder={step.placeholder ?? ""}
                      disabled={!canSubmit || isSubmitting}
                      className="min-h-[180px] w-full rounded-[1rem] border border-[var(--pv-border)] bg-white/90 px-3 py-3 text-sm text-zinc-900 outline-none transition focus:border-zinc-400"
                    />
                  </div>
                ) : null}

                {step.feedback ? (
                  <div className="mt-4 rounded-[1rem] border border-emerald-200 bg-emerald-50/70 p-4 text-sm text-emerald-950">
                    <p className="font-semibold">{step.feedback.verdict} · {step.feedback.score}/{step.feedback.pass_score}</p>
                    {step.feedback.strengths.length > 0 ? (
                      <ul className="mt-2 grid gap-1 text-emerald-900">
                        {step.feedback.strengths.map((item) => (
                          <li key={`${step.slug}-strength-${item}`}>• {item}</li>
                        ))}
                      </ul>
                    ) : null}
                    {step.feedback.improvements.length > 0 ? (
                      <ul className="mt-2 grid gap-1 text-amber-900">
                        {step.feedback.improvements.map((item) => (
                          <li key={`${step.slug}-improvement-${item}`}>• {item}</li>
                        ))}
                      </ul>
                    ) : null}
                    {step.feedback.revisit.length > 0 ? (
                      <ul className="mt-2 grid gap-1 text-zinc-800">
                        {step.feedback.revisit.map((item) => (
                          <li key={`${step.slug}-revisit-${item}`}>• {item}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}

                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => void handleSubmit(step)}
                    disabled={isSubmitting || !canSubmit}
                    className="pv-button-primary !w-auto disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isSubmitting ? t("learn.checking") : step.completed ? t("learn.retryStep") : t("learn.checkStep")}
                  </button>

                  <span className="text-xs text-zinc-500">
                    {t("learn.attempts")}: {step.attempts} · {t("learn.attemptsHint")}
                  </span>
                </div>
              </article>
            );
          })}
        </div>

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
