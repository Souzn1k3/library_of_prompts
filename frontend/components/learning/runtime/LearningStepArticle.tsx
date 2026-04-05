"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LearningStepChoiceInput } from "@/components/learning/runtime/LearningStepChoiceInput";
import { LearningStepFeedbackPanel } from "@/components/learning/runtime/LearningStepFeedbackPanel";
import { LearningStepTextInput } from "@/components/learning/runtime/LearningStepTextInput";
import type { StepState } from "@/components/learning/runtime/types";

type LearningStepArticleProps = {
  activeStep: StepState;
  activeStepIndex: number;
  stepsCount: number;
  previousStep: StepState | null;
  nextStep: StepState | null;
  canSubmit: boolean;
  isSubmitting: boolean;
  selectedChoiceId: string;
  textAnswer: string;
  stepHref: (stepSlug: string) => string;
  onChoiceChange: (choiceId: string) => void;
  onTextChange: (value: string) => void;
  onSubmitStep: () => void;
};

export function LearningStepArticle({
  activeStep,
  activeStepIndex,
  stepsCount,
  previousStep,
  nextStep,
  canSubmit,
  isSubmitting,
  selectedChoiceId,
  textAnswer,
  stepHref,
  onChoiceChange,
  onTextChange,
  onSubmitStep,
}: LearningStepArticleProps) {
  const { t } = useI18n();

  return (
    <article className="pv-panel px-6 py-6 sm:px-7 ring-1 ring-[var(--pv-brand)]/40">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="pv-kicker">{t(`learn.stepKind.${activeStep.kind}`)}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {t("learn.stepPosition", { current: activeStepIndex + 1, total: stepsCount })}
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
        <LearningStepChoiceInput
          step={activeStep}
          selectedChoiceId={selectedChoiceId}
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

      <LearningStepFeedbackPanel step={activeStep} />

      <div className="mt-5 flex flex-wrap items-center gap-3">
        {previousStep ? (
          <Link href={stepHref(previousStep.slug)} className="pv-button-secondary !w-auto">
            {t("learn.previousStep")}
          </Link>
        ) : null}

        <button
          type="button"
          onClick={onSubmitStep}
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
  );
}
