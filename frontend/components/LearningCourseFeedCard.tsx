import Link from "next/link";

import { T } from "@/components/i18n/T";
import { appRoute } from "@/lib/constants/routes";
import { getDifficultyTranslationKey } from "@/lib/i18n";
import type { LearningCourseCard } from "@/lib/types";

type LearningCourseFeedCardProps = {
  course: LearningCourseCard;
};

export function LearningCourseFeedCard({ course }: LearningCourseFeedCardProps) {
  const destination = course.resume_href
    ? course.resume_href
    : course.next_lesson_slug
      ? appRoute.learnCourseLesson(course.slug, course.next_lesson_slug)
      : appRoute.learnCourse(course.slug);

  const actionKey = course.status === "not_started" ? "home.startLearning" : "learn.continue";
  const statusKey = course.status === "completed" ? "learn.completed" : course.status === "active" ? "learn.inProgress" : "learn.recommended";

  return (
    <Link href={destination} prefetch={false} className="pv-card pv-card-optimized group block p-5">
      <div className="relative flex h-full flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <span className="pv-badge border-[rgba(37,99,235,0.18)] bg-[rgba(37,99,235,0.1)] text-[var(--pv-brand-strong)]">
              <T k="learn.course" />
            </span>
            <span className="pv-badge">
              <T k={getDifficultyTranslationKey(course.difficulty)} />
            </span>
          </div>
          <span className="pv-chip-brand">{course.progress_percent}%</span>
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-[-0.04em] text-zinc-950 transition group-hover:text-[var(--pv-brand-strong)]">
            {course.title}
          </h2>
          <p className="line-clamp-3 text-sm leading-relaxed text-zinc-600">
            {course.result_headline || course.description}
          </p>
        </div>

        <div className="mt-auto flex flex-wrap gap-2 text-xs text-zinc-500">
          <span className="pv-chip">
            <T k="learn.modulesShort" />: {course.module_count}
          </span>
          <span className="pv-chip">
            <T k="learn.lessonsShort" />: {course.lesson_count}
          </span>
          <span className="pv-chip">
            <T k="learn.effortShort" />: {course.estimated_minutes}m
          </span>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-[var(--pv-border)] pt-4">
          <p className="text-xs text-zinc-500">
            <T k={statusKey} />
          </p>
          <span className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
            <T k={actionKey} />
            <span aria-hidden="true">↗</span>
          </span>
        </div>
      </div>
    </Link>
  );
}
