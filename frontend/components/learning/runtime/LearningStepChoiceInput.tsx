"use client";

import type { StepState } from "@/components/learning/runtime/types";

type LearningStepChoiceInputProps = {
  step: StepState;
  selectedChoiceId: string;
  canSubmit: boolean;
  isSubmitting: boolean;
  onSelectChoice: (choiceId: string) => void;
};

export function LearningStepChoiceInput({
  step,
  selectedChoiceId,
  canSubmit,
  isSubmitting,
  onSelectChoice,
}: LearningStepChoiceInputProps) {
  return (
    <fieldset className="mt-4 grid gap-2">
      {step.question ? <legend className="text-sm font-medium text-zinc-900">{step.question}</legend> : null}
      {step.choices.map((choice) => (
        <label
          key={choice.id}
          className={`flex cursor-pointer items-start gap-2 rounded-[0.9rem] border px-3 py-2 text-sm transition ${
            selectedChoiceId === choice.id
              ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-900"
              : "border-[var(--pv-border)] bg-white/80 text-zinc-700"
          }`}
        >
          <input
            type="radio"
            name={`choice-${step.slug}`}
            className="mt-[0.2rem]"
            checked={selectedChoiceId === choice.id}
            onChange={() => onSelectChoice(choice.id)}
            disabled={!canSubmit || isSubmitting}
          />
          <span>
            <span>{choice.text}</span>
            {choice.explanation ? <span className="mt-1 block text-xs text-zinc-500">{choice.explanation}</span> : null}
          </span>
        </label>
      ))}
    </fieldset>
  );
}
