import Link from "next/link";

import { T } from "@/components/i18n/T";
import { appRoute } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";
import type { LearningMyCourseItem, LearningWeakArea } from "@/lib/types";

function formatDate(value: string | null | undefined, locale: string): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(parsed);
}

function formatBadgeLabel(language: Language, badgeCode: string | null | undefined): string {
  if (!badgeCode) {
    return "badge";
  }
  return getTranslation(language, badgeCode);
}

export function ActiveCourseCard({
  course,
  locale,
}: {
  course: LearningMyCourseItem;
  locale: string;
}) {
  return (
    <article className="pv-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{course.title}</p>
          <p className="mt-1 text-sm text-zinc-600">{course.subtitle}</p>
        </div>
        <span className="pv-chip-brand">{course.progress_percent}%</span>
      </div>

      <div className="mt-4 pv-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={course.progress_percent}>
        <div className="pv-progress-fill" style={{ width: `${course.progress_percent}%` }} />
      </div>

      <dl className="mt-4 grid gap-2 text-sm text-zinc-600">
        <div className="flex items-center justify-between gap-3">
          <dt>
            <T k="learn.lastActivity" />
          </dt>
          <dd>{formatDate(course.last_activity_at, locale)}</dd>
        </div>
        <div className="flex items-center justify-between gap-3">
          <dt>
            <T k="learn.nextLesson" />
          </dt>
          <dd className="text-right text-zinc-800">{course.next_lesson_title ?? "-"}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          href={course.continue_href ?? appRoute.learnCourse(course.slug)}
          className="pv-button-primary !w-auto"
        >
          <T k="learn.continue" />
        </Link>
        <Link href={appRoute.learnCourse(course.slug)} className="pv-button-secondary !w-auto">
          <T k="learn.openCourse" />
        </Link>
      </div>
    </article>
  );
}

export function CompletedCourseCard({
  course,
  language,
  locale,
}: {
  course: LearningMyCourseItem;
  language: Language;
  locale: string;
}) {
  return (
    <article className="pv-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{course.title}</p>
          <p className="mt-1 text-sm text-zinc-600">{course.subtitle}</p>
        </div>
        <span className="pv-chip-brand">100%</span>
      </div>

      <p className="mt-4 text-sm text-zinc-700">
        <T k="learn.completedOn" />: {formatDate(course.completed_at, locale)}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-zinc-600">
        <span className="pv-chip">{formatBadgeLabel(language, course.badge_code)}</span>
        {course.certificate_ready ? (
          <span className="pv-chip-brand">
            <T k="learn.certificateReady" />
          </span>
        ) : null}
      </div>

      <div className="mt-4 flex gap-3">
        <Link href={appRoute.learnCourse(course.slug)} className="pv-button-secondary !w-auto">
          <T k="learn.reviewCourse" />
        </Link>
      </div>
    </article>
  );
}

export function WeakAreaCard({ area }: { area: LearningWeakArea }) {
  return (
    <li className="pv-card p-4">
      <p className="text-sm font-semibold text-zinc-950">{area.tag}</p>
      <p className="mt-2 text-sm text-zinc-700">{area.recommendation}</p>
      {area.lesson_slug ? (
        <Link
          href={appRoute.learnBySlug(area.lesson_slug)}
          className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]"
        >
          <T k="learn.goToRecommendedLesson" />
          <span aria-hidden="true">↗</span>
        </Link>
      ) : null}
    </li>
  );
}
