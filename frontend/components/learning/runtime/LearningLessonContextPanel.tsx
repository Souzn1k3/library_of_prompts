"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { LearningCourseDetail, LearningLessonDetail } from "@/lib/types";

type LearningLessonContextPanelProps = {
  course: LearningCourseDetail;
  lesson: LearningLessonDetail;
};

function ContextList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="rounded-[1rem] border border-[var(--pv-border)] bg-white/85 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{title}</p>
      <ul className="mt-3 grid gap-2 text-sm leading-relaxed text-zinc-700">
        {items.map((item) => (
          <li key={`${title}-${item}`}>• {item}</li>
        ))}
      </ul>
    </section>
  );
}

export function LearningLessonContextPanel({
  course,
  lesson,
}: LearningLessonContextPanelProps) {
  const { t } = useI18n();

  const hasPrimary =
    Boolean(lesson.objective?.trim()) ||
    Boolean(lesson.deliverable?.trim()) ||
    Boolean(lesson.scenario_title?.trim()) ||
    Boolean(lesson.scenario_body?.trim()) ||
    Boolean(course.product_action);

  if (
    !hasPrimary &&
    lesson.debrief.length === 0 &&
    lesson.review_rubric.length === 0 &&
    lesson.common_mistakes.length === 0
  ) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker">{t("learn.lessonBlueprint")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {lesson.objective?.trim() || lesson.title}
          </h2>
          {lesson.deliverable?.trim() ? (
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              {t("learn.lessonDeliverable")}: {lesson.deliverable}
            </p>
          ) : null}
        </div>
      </div>

      {lesson.scenario_title || lesson.scenario_body || course.product_action ? (
        <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
          <section className="rounded-[1rem] border border-[var(--pv-border)] bg-white/90 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
              {t("learn.realWorldCase")}
            </p>
            {lesson.scenario_title ? (
              <p className="mt-2 text-sm font-semibold text-zinc-950">{lesson.scenario_title}</p>
            ) : null}
            {lesson.scenario_body ? (
              <p className="mt-2 text-sm leading-relaxed text-zinc-700">{lesson.scenario_body}</p>
            ) : null}
          </section>

          {course.product_action ? (
            <section className="rounded-[1rem] border border-[var(--pv-brand)]/20 bg-[var(--pv-brand-soft)]/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("learn.useInProduct")}
              </p>
              {course.product_action.body ? (
                <p className="mt-2 text-sm leading-relaxed text-zinc-700">{course.product_action.body}</p>
              ) : null}
              <Link href={course.product_action.href} className="pv-button-primary mt-4 !w-auto">
                {course.product_action.label}
              </Link>
            </section>
          ) : null}
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <ContextList title={t("learn.debriefTitle")} items={lesson.debrief} />
        <ContextList title={t("learn.reviewRubricTitle")} items={lesson.review_rubric} />
        <ContextList title={t("learn.commonMistakesTitle")} items={lesson.common_mistakes} />
      </div>
    </section>
  );
}
