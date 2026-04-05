"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningLessonStep } from "@/lib/types";

type LearningStepNavigationProps = {
  steps: LearningLessonStep[];
  activeStepIndex: number;
  stepHref: (stepSlug: string) => string;
};

export function LearningStepNavigation({
  steps,
  activeStepIndex,
  stepHref,
}: LearningStepNavigationProps) {
  const { t } = useI18n();

  return (
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
  );
}
