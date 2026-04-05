import Link from "next/link";

import { T } from "@/components/i18n/T";
import { getTranslation, type Language } from "@/lib/i18n";
import type { PopularLessonItem } from "@/lib/types";

type HomeLessonsSectionProps = {
  language: Language;
  lessons: PopularLessonItem[];
};

export function HomeLessonsSection({ language, lessons }: HomeLessonsSectionProps) {
  if (!lessons.length) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="learn.title" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            <T k="home.popularLessons" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="learn.subtitle" />
          </p>
        </div>
        <Link href="/learn" className="pv-inline-link">
          <T k="home.viewAllLessons" />
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {lessons.map((lesson) => (
          <Link
            key={`home-lesson-${lesson.id}`}
            href={`/learn/${encodeURIComponent(lesson.slug)}`}
            className="pv-card block p-5"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{lesson.title}</p>
                <p className="mt-2 text-sm text-zinc-600">
                  {lesson.completion_count} <T k="learn.completions" />
                </p>
              </div>
              <span className="pv-chip-brand">
                <T k={lesson.locked ? "learn.locked" : "learn.open"} />
              </span>
            </div>
            <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
              {getTranslation(language, "learn.openLesson")}
              <span aria-hidden="true">↗</span>
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
