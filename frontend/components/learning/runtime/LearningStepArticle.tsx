"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { evaluateTextDraft, getQuizQuestions } from "@/components/learning/runtime/helpers";
import { LearningStepChoiceInput } from "@/components/learning/runtime/LearningStepChoiceInput";
import { LearningStepFeedbackPanel } from "@/components/learning/runtime/LearningStepFeedbackPanel";
import { LearningStepTextInput } from "@/components/learning/runtime/LearningStepTextInput";
import type { StepState } from "@/components/learning/runtime/types";

type LearningStepArticleProps = {
  activeStep: StepState;
  activeStepIndex: number;
  stepsCount: number;
  completedStepsCount: number;
  previousStep: StepState | null;
  nextStep: StepState | null;
  theoryStepSlug: string | null;
  isFullscreen: boolean;
  canSubmit: boolean;
  isSubmitting: boolean;
  selectedChoiceAnswers: Record<string, string>;
  textAnswer: string;
  stepHref: (stepSlug: string) => string;
  onChoiceChange: (questionId: string, choiceId: string) => void;
  onTextChange: (value: string) => void;
  onSubmitStep: () => void;
};

function CriteriaItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <li className="flex items-start justify-between gap-2 rounded-[0.9rem] border border-[var(--pv-border)] bg-white/80 px-3 py-2 text-xs text-zinc-700">
      <span className="font-medium text-zinc-900">{label}</span>
      <span className="text-right">{value}</span>
    </li>
  );
}

function ChecklistRow({
  ok,
  label,
}: {
  ok: boolean;
  label: string;
}) {
  return (
    <li
      className={`rounded-[0.85rem] border px-3 py-2 text-xs ${
        ok
          ? "border-emerald-200 bg-emerald-50 text-emerald-900"
          : "border-amber-200 bg-amber-50 text-amber-900"
      }`}
    >
      {ok ? "✓" : "•"} {label}
    </li>
  );
}

export function LearningStepArticle({
  activeStep,
  activeStepIndex,
  stepsCount,
  completedStepsCount,
  previousStep,
  nextStep,
  theoryStepSlug,
  isFullscreen,
  canSubmit,
  isSubmitting,
  selectedChoiceAnswers,
  textAnswer,
  stepHref,
  onChoiceChange,
  onTextChange,
  onSubmitStep,
}: LearningStepArticleProps) {
  const { t } = useI18n();
  const isPracticeStep =
    activeStep.kind === "guided_practice" ||
    activeStep.kind === "applied_exercise" ||
    activeStep.kind === "reflection";
  const textDiagnostics =
    activeStep.submission_type === "text" ? evaluateTextDraft(activeStep, textAnswer) : null;
  const isMarkedLearned = activeStep.submission_type === "none" && activeStep.completed;
  const quizQuestions = activeStep.submission_type === "choice" ? getQuizQuestions(activeStep) : [];
  const hasAnsweredAllQuizQuestions =
    activeStep.submission_type !== "choice" ||
    quizQuestions.every((question) => (selectedChoiceAnswers[question.id] ?? "").trim().length > 0);
  const submitDisabled =
    isSubmitting ||
    !canSubmit ||
    !activeStep.unlocked ||
    isMarkedLearned ||
    (activeStep.submission_type === "choice" && !hasAnsweredAllQuizQuestions) ||
    (activeStep.submission_type === "text" && textAnswer.trim().length === 0);

  const submitLabel = isSubmitting
    ? t("learn.checking")
    : activeStep.submission_type === "none"
      ? isMarkedLearned
        ? t("learn.completed")
        : t("learn.markStepLearned")
      : activeStep.completed
        ? t("learn.retryStep")
        : t("learn.checkStep");

  return (
    <article
      className={`pv-panel ring-1 ring-[var(--pv-brand)]/35 ${
        isFullscreen ? "px-5 py-5 sm:px-7 sm:py-7 lg:px-8 lg:py-8" : "px-6 py-6 sm:px-7"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-zinc-500">
            {t("learn.stepPosition", { current: activeStepIndex + 1, total: stepsCount })} ·{" "}
            {t("learn.stepCompletionValue", { done: completedStepsCount, total: stepsCount })}
          </p>
          <h3 className="mt-1 text-xl font-bold tracking-[-0.04em] text-zinc-950">{activeStep.title}</h3>
          {isPracticeStep && theoryStepSlug && theoryStepSlug !== activeStep.slug ? (
            <Link
              href={stepHref(theoryStepSlug)}
              className="mt-3 inline-flex items-center text-base font-semibold text-[var(--pv-brand-strong)] hover:text-[var(--pv-brand)]"
            >
              {"← "}
              {t("learn.backToTheory")}
            </Link>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="pv-chip-brand">{t("learn.stepMinutesLabel", { count: activeStep.estimated_minutes })}</span>
        </div>
      </div>

      {!activeStep.unlocked ? (
        <div className="mt-4 rounded-[1rem] border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-950">
          {t("learn.completePreviousStepFirst")}
        </div>
      ) : null}

      <div className={`mt-5 space-y-4 ${isFullscreen ? "mx-auto w-full max-w-[1180px]" : ""}`}>
        {!isPracticeStep && activeStep.content.length > 0 ? (
          <section>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("learn.theoryShort")}</p>
            <div className="mt-2 space-y-3 text-sm leading-relaxed text-zinc-700">
              {activeStep.content.map((line, lineIdx) => (
                <p key={`${activeStep.slug}-content-${lineIdx}`}>{line}</p>
              ))}
            </div>
          </section>
        ) : null}

        {activeStep.task ? (
          <section className="rounded-[1.1rem] border border-[var(--pv-border)] bg-white/80 p-4 text-sm text-zinc-700">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("learn.practiceAction")}</p>
            {isPracticeStep ? <p className="mt-2 text-sm text-zinc-600">{t("learn.practiceFocusHint")}</p> : null}
            <p className="mt-2">{activeStep.task}</p>
          </section>
        ) : null}

        <section className="rounded-[1rem] border border-[var(--pv-border)] bg-white/85 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("learn.successCriteria")}</p>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            <CriteriaItem label={t("learn.passScoreShort")} value={`${activeStep.pass_score}/100`} />
            {activeStep.submission_type === "text" && activeStep.min_words ? (
              <CriteriaItem label={t("learn.minWords")} value={String(activeStep.min_words)} />
            ) : null}
            {activeStep.submission_type === "choice" ? (
              <CriteriaItem label={t("learn.answerType")} value={t("learn.singleChoice")} />
            ) : null}
            {activeStep.submission_type === "choice" && quizQuestions.length > 1 ? (
              <CriteriaItem label={t("learn.quizQuestions")} value={String(quizQuestions.length)} />
            ) : null}
            {activeStep.required_markers.length > 0 ? (
              <CriteriaItem label={t("learn.requiredMarkers")} value={activeStep.required_markers.join(", ")} />
            ) : null}
            {activeStep.forbidden_phrases.length > 0 ? (
              <CriteriaItem label={t("learn.avoidPhrases")} value={activeStep.forbidden_phrases.join(", ")} />
            ) : null}
          </ul>
        </section>

        {activeStep.submission_type === "choice" ? (
          <LearningStepChoiceInput
            step={activeStep}
            selectedChoiceAnswers={selectedChoiceAnswers}
            canSubmit={canSubmit}
            isSubmitting={isSubmitting}
            onSelectChoice={onChoiceChange}
          />
        ) : null}

        {activeStep.submission_type === "text" ? (
          <LearningStepTextInput
            step={activeStep}
            textAnswer={textAnswer}
            canSubmit={canSubmit}
            isSubmitting={isSubmitting}
            onTextChange={onTextChange}
          />
        ) : null}

        {textDiagnostics ? (
          <section className="rounded-[1rem] border border-[var(--pv-border)] bg-white/85 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("learn.precheck")}</p>
            <ul className="mt-3 grid gap-2 sm:grid-cols-2">
              <ChecklistRow
                ok={textDiagnostics.wordCount >= textDiagnostics.minWords}
                label={t("learn.precheckWords", {
                  current: textDiagnostics.wordCount,
                  min: textDiagnostics.minWords,
                })}
              />
              <ChecklistRow
                ok={textDiagnostics.missingMarkers.length === 0}
                label={
                  textDiagnostics.missingMarkers.length === 0
                    ? t("learn.precheckMarkersOk")
                    : t("learn.precheckMarkersMissing", {
                        markers: textDiagnostics.missingMarkers.join(", "),
                      })
                }
              />
              {textDiagnostics.forbiddenHits.length > 0 ? (
                <ChecklistRow
                  ok={false}
                  label={t("learn.precheckForbiddenHit", {
                    markers: textDiagnostics.forbiddenHits.join(", "),
                  })}
                />
              ) : null}
              <ChecklistRow
                ok={!textDiagnostics.looksLowSignal && textDiagnostics.lowSignalMarkers.length === 0}
                label={
                  textDiagnostics.lowSignalMarkers.length > 0
                    ? t("learn.precheckSpecificityWeakMarkers", {
                        markers: textDiagnostics.lowSignalMarkers.join(", "),
                      })
                    : textDiagnostics.looksLowSignal
                      ? t("learn.precheckSpecificityWeak")
                      : t("learn.precheckSpecificityOk")
                }
              />
            </ul>
          </section>
        ) : null}

        <LearningStepFeedbackPanel step={activeStep} />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        {previousStep ? (
          <Link href={stepHref(previousStep.slug)} className="pv-button-secondary !w-auto">
            {t("learn.previousStep")}
          </Link>
        ) : null}

        <button
          type="button"
          onClick={onSubmitStep}
          disabled={submitDisabled}
          className={`pv-button-primary !w-auto disabled:cursor-not-allowed disabled:opacity-60 ${
            isMarkedLearned ? "pv-button-primary-disabled" : ""
          }`}
        >
          {submitLabel}
        </button>

        {nextStep ? (
          nextStep.unlocked ? (
            <Link href={stepHref(nextStep.slug)} className="pv-button-secondary !w-auto">
              {t("learn.nextStep")}
            </Link>
          ) : (
            <span className="rounded-full border border-zinc-200 bg-zinc-100 px-4 py-2 text-xs font-semibold text-zinc-500">
              {t("learn.completeCurrentStepFirst")}
            </span>
          )
        ) : null}

        <span className="text-xs text-zinc-500">
          {t("learn.attempts")}: {activeStep.attempts} · {t("learn.attemptsHint")}
        </span>
      </div>
    </article>
  );
}

