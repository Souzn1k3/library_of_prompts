"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningLessonStep } from "@/lib/types";

type LearningStepNavigationProps = {
  steps: LearningLessonStep[];
  activeStepIndex: number;
  stepHref: (stepSlug: string) => string;
};

function stepStateLabel(step: LearningLessonStep, activeStepIndex: number, index: number, t: (k: string) => string): string {
  if (index === activeStepIndex) {
    return t("learn.current");
  }
  if (step.completed) {
    return t("learn.completed");
  }
  if (!step.unlocked) {
    return t("learn.locked");
  }
  return t("learn.open");
}

export function LearningStepNavigation({
  steps,
  activeStepIndex,
  stepHref,
}: LearningStepNavigationProps) {
  const { t } = useI18n();

  return (
    <nav>
      <ol className="grid gap-2 md:grid-cols-2">
        {steps.map((step, index) => {
          const isActive = index === activeStepIndex;
          const stateLabel = stepStateLabel(step, activeStepIndex, index, t);
          const cardClass = isActive
            ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-950"
            : step.unlocked
              ? "border-[var(--pv-border)] bg-white/90 text-zinc-700 hover:border-zinc-300"
              : "border-[var(--pv-border)] bg-zinc-100/70 text-zinc-400";

          const body = (
            <div className={`rounded-[1rem] border px-3 py-3 transition ${cardClass}`} aria-current={isActive ? "step" : undefined}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold">
                  {index + 1}. {step.title}
                </p>
                <span className="text-[11px] uppercase tracking-[0.1em]">{stateLabel}</span>
              </div>
              <p className="mt-1 text-xs">
                {t(`learn.stepKind.${step.kind}`)} · {t("learn.stepMinutesLabel", { count: step.estimated_minutes })}
              </p>
            </div>
          );

          return (
            <li key={step.slug}>
              {step.unlocked ? <Link href={stepHref(step.slug)}>{body}</Link> : body}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
