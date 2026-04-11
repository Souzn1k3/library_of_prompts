import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { TokenAmount } from "@/components/ui/TokenAmount";
import { APP_ROUTES } from "@/lib/constants/routes";
import {
  getDifficultyTranslationKey,
  getTranslation,
  type Language,
} from "@/lib/i18n";
import type { LearningLessonOutline } from "@/lib/types";

import type { LearningCoursePageData } from "./learning-course-page-data";

type LearningCoursePageViewProps = {
  language: Language;
  data: LearningCoursePageData;
};

function lessonStateLabel(language: Language, lesson: LearningLessonOutline): string {
  if (lesson.status === "completed") {
    return getTranslation(language, "learn.completed");
  }
  if (lesson.status === "in_progress") {
    return getTranslation(language, "learn.inProgress");
  }
  if (!lesson.unlocked) {
    return getTranslation(language, "learn.locked");
  }
  return getTranslation(language, "learn.open");
}

export function LearningCoursePageView({ language, data }: LearningCoursePageViewProps) {
  const { course, primaryHref } = data;
  const outcomeItems = course.what_you_will_learn.filter(Boolean);

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
      >
        {outcomeItems.length > 0 ? (
          <section className="max-w-3xl">
            <h2 className="text-base font-semibold text-zinc-900">
              <T k="learn.whatYouWillLearn" />
            </h2>
            <ul className="mt-2 grid gap-1.5 text-base leading-relaxed text-zinc-700">
              {outcomeItems.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </section>
        ) : null}
        <div className="pv-cta-group">
          <Link href={primaryHref} className="pv-button-primary">
            {course.start_or_continue_label}
          </Link>
          <Link href={APP_ROUTES.learnMy} className="pv-button-secondary">
            <T k="learn.myModules" />
          </Link>
        </div>
      </PageIntro>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-600">
          <span className="pv-chip">
            {getTranslation(language, getDifficultyTranslationKey(course.difficulty))}
          </span>
          <span className="pv-chip-brand">
            {course.status === "completed"
              ? getTranslation(language, "learn.completed")
              : getTranslation(language, "learn.inProgress")}
          </span>
          <span className="pv-chip">
            <T k="learn.progress" />: {course.progress_percent}%
          </span>
          <span className="pv-chip">
            <T k="learn.modulesShort" />: {course.module_count} · <T k="learn.lessonsShort" />: {course.lesson_count}
          </span>
          <span className="pv-chip">
            <T k="learn.estimatedEffort" />: {course.estimated_minutes}m
          </span>
        </div>

        <div
          className="mt-5 pv-progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={course.progress_percent}
        >
          <div className="pv-progress-fill" style={{ width: `${course.progress_percent}%` }} />
        </div>

        {course.result_headline ? (
          <div className="mt-5 rounded-[1rem] border border-[var(--pv-brand)]/20 bg-[var(--pv-brand-soft)]/60 px-4 py-4 text-sm leading-relaxed text-zinc-700">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
              <T k="learn.resultHeadlineTitle" />
            </p>
            <p className="mt-2">{course.result_headline}</p>
          </div>
        ) : null}
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              <T k="learn.moduleStructure" />
            </h2>
            <p className="mt-2 text-sm text-zinc-600">
              <T k="learn.moduleStructureBody" />
            </p>
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

              <div
                className="mt-4 pv-progress"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={module.progress_percent}
              >
                <div className="pv-progress-fill" style={{ width: `${module.progress_percent}%` }} />
              </div>

              <ol className="mt-4 grid gap-3">
                {module.lessons.map((lesson) => (
                  <li
                    key={lesson.slug}
                    className="rounded-[1.1rem] border border-[var(--pv-border)] bg-white/85 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-zinc-950">
                          {lesson.position}. {lesson.title}
                        </p>
                        <p className="mt-1 text-sm text-zinc-600">{lesson.summary}</p>
                        <p className="mt-2 text-xs text-zinc-500">
                          {lesson.estimated_minutes}m · {lessonStateLabel(language, lesson)} · {lesson.progress_percent}%
                        </p>
                      </div>
                      {lesson.is_final_assessment ? (
                        <span className="pv-chip-brand">
                          {getTranslation(language, "learn.finalAssessment")}
                        </span>
                      ) : null}
                    </div>

                    <div className="mt-3 flex flex-wrap gap-3">
                      <Link
                        href={lesson.continue_href}
                        className={`pv-button-secondary !w-auto ${lesson.unlocked ? "" : "pointer-events-none opacity-50"}`}
                      >
                        {lesson.unlocked
                          ? getTranslation(language, "learn.openLesson")
                          : getTranslation(language, "learn.locked")}
                      </Link>
                    </div>
                  </li>
                ))}
              </ol>
            </article>
          ))}
        </div>
      </section>

      {course.weak_areas.length > 0 ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <p className="text-sm font-semibold text-zinc-900">
            <T k="learn.recommendedFocus" />
          </p>
          <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
            {course.weak_areas.map((area) => (
              <li key={`${area.tag}-${area.lesson_slug ?? "none"}`}>• {area.recommendation}</li>
            ))}
          </ul>
        </section>
      ) : null}

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
            {course.rewards.course_completed
              ? getTranslation(language, "learn.completed")
              : getTranslation(language, "learn.inProgress")}
          </span>
        </div>
      </section>
    </div>
  );
}

