"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningLessonDetail } from "@/lib/types";
import type { StepState } from "@/components/learning/runtime/types";

type LessonOutlineSidebarProps = {
  lesson: LearningLessonDetail;
  courseTitle: string;
  returnToCourseHref: string;
  courseProgressPercent: number;
  steps: StepState[];
  activeStepIndex: number;
  stepHref: (stepSlug: string) => string;
  onOpenFullscreen: () => void;
};

function lessonStateLabel(
  item: LearningLessonDetail["lesson_list"][number],
  currentSlug: string,
  t: (key: string) => string,
): string {
  if (item.slug === currentSlug) {
    return t("learn.current");
  }
  if (item.status === "completed") {
    return t("learn.completed");
  }
  if (!item.unlocked) {
    return t("learn.locked");
  }
  return t("learn.open");
}

export function LessonOutlineSidebar({
  lesson,
  courseTitle,
  returnToCourseHref,
  courseProgressPercent,
  steps,
  activeStepIndex,
  stepHref,
  onOpenFullscreen,
}: LessonOutlineSidebarProps) {
  const { t } = useI18n();
  const completedLessons = lesson.lesson_list.filter((item) => item.status === "completed").length;
  const remainingLessons = Math.max(lesson.lesson_list.length - completedLessons, 0);

  return (
    <aside className="pv-panel px-5 py-5 lg:sticky lg:top-0">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-500">{t("learn.course")}</p>
          <p className="mt-1 truncate text-sm font-semibold text-zinc-900" title={courseTitle}>
            {courseTitle}
          </p>
          <Link
            href={returnToCourseHref}
            className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-[var(--pv-brand-strong)] hover:underline"
          >
            <span aria-hidden="true">←</span>
            {t("learn.returnToCourse")}
          </Link>
        </div>
        <span className="pv-chip-brand shrink-0">{courseProgressPercent}%</span>
      </div>

      <div className="mt-4 rounded-[1rem] border border-[var(--pv-border)] bg-white/85 px-3 py-3 text-xs text-zinc-700">
        <p className="font-semibold text-zinc-900">
          {t("learn.lessonPositionLabel", { current: lesson.position_in_course, total: lesson.total_lessons })}
        </p>
        <p className="mt-1">
          {t("learn.remainingLessonsHint", {
            count: remainingLessons,
          })}
        </p>
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

      <details className="mt-4 overflow-hidden rounded-[1rem] border border-[var(--pv-border)] bg-white/85 px-3 py-3">
        <summary className="cursor-pointer select-none text-sm font-semibold text-zinc-900">
          {t("learn.lessonList")}
        </summary>
        <ol className="mt-3 grid gap-2">
          {lesson.lesson_list.map((item) => {
            const isCurrent = item.slug === lesson.lesson_slug;
            const label = lessonStateLabel(item, lesson.lesson_slug, t);
            const className = isCurrent
              ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-900"
              : item.unlocked
                ? "border-[var(--pv-border)] bg-white/90 text-zinc-700 hover:border-zinc-300"
                : "pointer-events-none border-[var(--pv-border)] bg-zinc-100/60 text-zinc-400";

            return (
              <li key={item.slug}>
                <Link
                  href={item.continue_href}
                  className={`block min-w-0 rounded-[1rem] border px-3 py-2 text-sm transition ${className}`}
                >
                  <div className="flex min-w-0 items-start justify-between gap-2">
                    <span className="min-w-0 flex-1 truncate" title={`${item.position}. ${item.title}`}>
                      {item.position}. {item.title}
                    </span>
                    <span className="hidden shrink-0 text-[11px] uppercase tracking-[0.08em] sm:inline">{label}</span>
                  </div>
                  <p className="mt-1 text-xs">{item.progress_percent}%</p>
                </Link>
                {isCurrent ? (
                  <ol className="ml-3 mt-2 grid gap-1.5 border-l border-[var(--pv-border)] pl-2">
                    {steps.map((step, index) => {
                      const isActiveStep = index === activeStepIndex;
                      const state = isActiveStep
                        ? t("learn.current")
                        : step.completed
                          ? t("learn.completed")
                          : step.unlocked
                            ? t("learn.open")
                            : t("learn.locked");
                      const stepClass = isActiveStep
                        ? "border-[var(--pv-brand)] bg-[var(--pv-brand-soft)] text-zinc-900"
                        : step.unlocked
                          ? "border-[var(--pv-border)] bg-white/85 text-zinc-700"
                          : "border-[var(--pv-border)] bg-zinc-100/70 text-zinc-400";
                      const stepBody = (
                        <div className={`rounded-[0.85rem] border px-2.5 py-2 text-xs ${stepClass}`}>
                          <div className="flex items-start justify-between gap-2">
                            <span className="min-w-0 truncate font-medium">
                              {index + 1}. {step.title}
                            </span>
                            <span className="shrink-0 uppercase tracking-[0.08em]">{state}</span>
                          </div>
                        </div>
                      );

                      return (
                        <li key={step.slug}>
                          {step.unlocked ? <Link href={stepHref(step.slug)}>{stepBody}</Link> : stepBody}
                        </li>
                      );
                    })}
                  </ol>
                ) : null}
              </li>
            );
          })}
        </ol>
      </details>

      <button type="button" onClick={onOpenFullscreen} className="mt-3 pv-button-secondary !w-full">
        {t("learn.openFullscreen")}
      </button>
    </aside>
  );
}
