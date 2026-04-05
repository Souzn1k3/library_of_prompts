import Link from "next/link";
import type { ReactNode } from "react";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { TokenAmount } from "@/components/ui/TokenAmount";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTranslation, type Language } from "@/lib/i18n";

import type { LearningCoursePageData } from "./learning-course-page-data";

type LearningCoursePageViewProps = {
  language: Language;
  data: LearningCoursePageData;
};

function CourseStatCard({ label, value }: { label: ReactNode; value: ReactNode }) {
  return (
    <div className="pv-card p-4">
      <p className="text-xs uppercase tracking-[0.08em] text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{value}</p>
    </div>
  );
}

export function LearningCoursePageView({ language, data }: LearningCoursePageViewProps) {
  const { course, primaryHref } = data;

  return (
    <div className="pv-page">
      <PageIntro
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
          { label: getTranslation(language, "nav.learn"), href: APP_ROUTES.learn },
          { label: course.title },
        ]}
        eyebrow={<T k="learn.course" />}
        title={course.title}
        description={course.description}
        hint={course.subtitle}
        actions={
          <>
            <Link href={primaryHref} className="pv-button-primary">
              {course.start_or_continue_label}
            </Link>
            <Link href={APP_ROUTES.learnMy} className="pv-button-secondary">
              <T k="learn.myModules" />
            </Link>
          </>
        }
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <CourseStatCard label={<T k="learn.progress" />} value={`${course.progress_percent}%`} />
          <CourseStatCard label={<T k="learn.modulesTitle" />} value={course.module_count} />
          <CourseStatCard label={<T k="learn.lessonCount" />} value={course.lesson_count} />
          <CourseStatCard label={<T k="learn.estimatedEffort" />} value={`${course.estimated_minutes}m`} />
        </div>

        <div className="mt-5 pv-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={course.progress_percent}>
          <div className="pv-progress-fill" style={{ width: `${course.progress_percent}%` }} />
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              <T k="learn.whatYouWillLearn" />
            </h2>
          </div>
        </div>
        <ul className="mt-6 grid gap-3">
          {course.what_you_will_learn.map((item) => (
            <li key={item} className="pv-card p-4 text-sm leading-relaxed text-zinc-700">
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              <T k="learn.moduleStructure" />
            </h2>
          </div>
        </div>

        <div className="mt-6 grid gap-4">
          {course.modules.map((module) => (
            <article key={module.slug} className="pv-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold tracking-[-0.04em] text-zinc-950">{module.title}</h3>
                  <p className="mt-1 text-sm text-zinc-600">{module.summary}</p>
                </div>
                <span className="pv-chip-brand">{module.progress_percent}%</span>
              </div>

              <div className="mt-4 pv-progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={module.progress_percent}>
                <div className="pv-progress-fill" style={{ width: `${module.progress_percent}%` }} />
              </div>

              <ol className="mt-5 grid gap-3">
                {module.lessons.map((lesson) => (
                  <li key={lesson.slug} className="rounded-[1.2rem] border border-[var(--pv-border)] bg-white/80 px-4 py-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-zinc-950">{lesson.position}. {lesson.title}</p>
                        <p className="mt-1 text-sm text-zinc-600">{lesson.summary}</p>
                        <p className="mt-2 text-xs text-zinc-500">{lesson.estimated_minutes}m</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`pv-chip ${lesson.is_final_assessment ? "pv-chip-brand" : ""}`}>
                          {lesson.is_final_assessment ? getTranslation(language, "learn.finalAssessment") : getTranslation(language, "learn.lesson")}
                        </span>
                        <span className="pv-chip-brand">{lesson.progress_percent}%</span>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-3">
                      <Link
                        href={lesson.continue_href}
                        className={`pv-button-secondary !w-auto ${lesson.unlocked ? "" : "pointer-events-none opacity-50"}`}
                      >
                        {lesson.unlocked ? getTranslation(language, "learn.openLesson") : getTranslation(language, "learn.locked")}
                      </Link>
                    </div>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-zinc-900">
              <T k="learn.courseRewards" />
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-zinc-600">
              <span className="inline-flex items-center gap-2">
                <T k="learn.lessonReward" />:
                <TokenAmount amount={`+${course.rewards.lesson_reward_lmn}`} />
              </span>
              <span className="inline-flex items-center gap-2">
                <T k="learn.courseReward" />:
                <TokenAmount amount={`+${course.rewards.course_reward_lmn}`} />
              </span>
            </div>
            <p className="mt-1 text-xs text-zinc-500">
              <T k="learn.badge" />: {course.rewards.badge_code}
            </p>
          </div>
          <span className={`pv-chip-brand ${course.rewards.course_completed ? "" : "opacity-80"}`}>
            {course.rewards.course_completed ? getTranslation(language, "learn.completed") : getTranslation(language, "learn.inProgress")}
          </span>
        </div>
      </section>
    </div>
  );
}
