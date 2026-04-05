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
          className="flex cursor-pointer items-start gap-2 rounded-[0.9rem] border border-[var(--pv-border)] bg-white/80 px-3 py-2 text-sm text-zinc-700"
        >
          <input
            type="radio"
            name={`choice-${step.slug}`}
            className="mt-[0.2rem]"
            checked={selectedChoiceId === choice.id}
            onChange={() => onSelectChoice(choice.id)}
            disabled={!canSubmit || isSubmitting}
          />
          <span>{choice.text}</span>
        </label>
      ))}
    </fieldset>
  );
}
