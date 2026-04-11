"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { suggestedTemplate } from "@/components/learning/runtime/helpers";
import type { StepState } from "@/components/learning/runtime/types";

type LearningStepTextInputProps = {
  step: StepState;
  textAnswer: string;
  canSubmit: boolean;
  isSubmitting: boolean;
  onTextChange: (value: string) => void;
};

export function LearningStepTextInput({
  step,
  textAnswer,
  canSubmit,
  isSubmitting,
  onTextChange,
}: LearningStepTextInputProps) {
  const { t } = useI18n();
  const showPromptEnglishHint = step.kind !== "reflection";
  const template = suggestedTemplate(step, t);

  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs text-zinc-500">{t("learn.answerFormatHint")}</p>
      {showPromptEnglishHint ? (
        <div className="rounded-[0.9rem] border border-zinc-200/80 bg-zinc-50/75 px-3 py-2 text-xs text-zinc-500">
          {t("learn.promptEnglishHint")}
        </div>
      ) : null}
      {step.kind === "reflection" ? (
        <div className="rounded-[0.9rem] border border-[var(--pv-border)] bg-zinc-50/80 px-3 py-2 text-xs text-zinc-600">
          <p className="pv-hint-badge">{t("common.hintBadge")}</p>
          <p className="mt-1">{t("learn.reflectionHint")}</p>
        </div>
      ) : null}
      {template ? (
        <div className="rounded-[1rem] border border-[var(--pv-border)] bg-zinc-50/90 px-3 py-3 text-xs text-zinc-700">
          <p className="pv-hint-badge">{t("learn.readyPrompt")}</p>
          <p className="mt-1 text-zinc-600">{t("learn.readyPromptHint")}</p>
          <pre className="mt-3 whitespace-pre-wrap font-mono text-[12px] leading-6 text-zinc-800">{template}</pre>
        </div>
      ) : null}
      <textarea
        value={textAnswer}
        onChange={(event) => onTextChange(event.target.value)}
        placeholder={template ?? ""}
        disabled={!canSubmit || isSubmitting}
        className="min-h-[180px] w-full resize-none rounded-[1rem] border border-[var(--pv-border)] bg-white/90 px-3 py-3 text-sm text-zinc-900 outline-none transition focus:border-zinc-400"
      />
    </div>
  );
}
