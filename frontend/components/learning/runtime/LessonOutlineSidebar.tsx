"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningLessonDetail } from "@/lib/types";

type LessonOutlineSidebarProps = {
  lesson: LearningLessonDetail;
  courseProgressPercent: number;
};

export function LessonOutlineSidebar({
  lesson,
  courseProgressPercent,
}: LessonOutlineSidebarProps) {
  const { t } = useI18n();

  return (
    <aside className="pv-panel px-5 py-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-zinc-900">{t("learn.lessonList")}</p>
        <span className="pv-chip-brand">{courseProgressPercent}%</span>
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
                <span className="truncate">
                  {item.position}. {item.title}
                </span>
                <span className="text-xs">{item.progress_percent}%</span>
              </div>
            </Link>
          </li>
        ))}
      </ol>
    </aside>
  );
}
