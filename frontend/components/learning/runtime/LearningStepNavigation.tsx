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
              <div className="flex min-w-0 items-start justify-between gap-2">
                <p className="min-w-0 flex-1 text-sm font-semibold leading-snug">
                  {index + 1}. {step.title}
                </p>
                <span className="hidden shrink-0 text-[11px] uppercase tracking-[0.1em] sm:inline">{stateLabel}</span>
              </div>
              <p className="mt-1 text-xs">
                {t(`learn.stepKind.${step.kind}`)} · {t("learn.stepMinutesLabel", { count: step.estimated_minutes })}
              </p>
              <span className="mt-2 inline-flex rounded-full border border-[var(--pv-border)] bg-white/75 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-zinc-500 sm:hidden">
                {stateLabel}
              </span>
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
