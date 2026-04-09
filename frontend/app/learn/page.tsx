import type { Metadata } from "next";
import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { TokenAmount } from "@/components/ui/TokenAmount";
import { ApiRequestError, fetchLearningCatalog } from "@/lib/api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getDifficultyTranslationKey, getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export const revalidate = 0;

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return buildPageMetadata({
    title: getTranslation(language, "meta.learnTitle"),
    description: getTranslation(language, "meta.learnDescription"),
    path: APP_ROUTES.learn,
  });
}

export default async function LearnIndexPage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const catalog = await fetchLearningCatalog(accessToken, language);

    return (
      <div className="pv-page">
        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
            { label: getTranslation(language, "nav.learn") },
          ]}
          eyebrow={<T k="learn.title" />}
          title={<T k="learn.title" />}
          description={<T k="learn.releaseSubtitle" />}
          actions={
            <>
              <Link href={APP_ROUTES.learnStart} className="pv-button-primary">
                <T k="home.startLearning" />
              </Link>
              <Link href={APP_ROUTES.learnMy} className="pv-button-secondary">
                <T k="learn.myModules" />
              </Link>
            </>
          }
        />

        <section className="grid gap-4 lg:grid-cols-3">
          {catalog.courses.map((course) => (
            <article key={`track-${course.slug}`} className="pv-card p-5">
              <p className="pv-kicker">{getTranslation(language, getDifficultyTranslationKey(course.difficulty))}</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">{course.title}</h2>
              <p className="mt-3 text-sm leading-relaxed text-zinc-600">
                {course.result_headline || course.description}
              </p>
            </article>
          ))}
        </section>

        {catalog.courses.length === 0 ? (
          <div className="pv-alert pv-alert-warning">
            <T k="learn.noLessons" />
          </div>
        ) : (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.05em] text-zinc-950">
                  <T k="learn.modulesTitle" />
                </h2>
                <p className="mt-2 text-sm text-zinc-600">
                  <T k="learn.catalogPathHint" />
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-4">
              {catalog.courses.map((course) => {
                const isRecommended = course.slug === catalog.recommended_course_slug;
                const destination = course.resume_href
                  ? course.resume_href
                  : course.next_lesson_slug
                    ? appRoute.learnCourseLesson(course.slug, course.next_lesson_slug)
                    : appRoute.learnCourse(course.slug);
                const ctaLabel =
                  course.status === "not_started"
                    ? getTranslation(language, "home.startLearning")
                    : getTranslation(language, "learn.continue");

                return (
                  <article key={course.slug} className="pv-card p-6">
                    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(16rem,0.8fr)] xl:items-start">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          {isRecommended ? <span className="pv-chip-brand"><T k="learn.recommended" /></span> : null}
                          <span className="pv-chip">
                            {getTranslation(language, getDifficultyTranslationKey(course.difficulty))}
                          </span>
                          <span className="pv-chip-brand">{course.progress_percent}%</span>
                        </div>
                        <h3 className="mt-4 text-2xl font-semibold tracking-[-0.05em] text-zinc-950">{course.title}</h3>
                        <p className="mt-2 text-sm text-zinc-600">{course.subtitle}</p>
                        <p className="mt-4 text-sm leading-relaxed text-zinc-700">{course.description}</p>
                        {course.result_headline ? (
                          <p className="mt-4 text-sm leading-relaxed text-zinc-700">{course.result_headline}</p>
                        ) : null}
                        {course.deliverable_preview ? (
                          <div className="mt-4 rounded-[1rem] border border-[var(--pv-border)] bg-white/80 px-4 py-4 text-sm text-zinc-700">
                            <span className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                              <T k="learn.deliverablePreviewTitle" />
                            </span>
                            <p className="mt-2">{course.deliverable_preview}</p>
                          </div>
                        ) : null}
                      </div>

                      <div className="space-y-4">
                        <div className="grid grid-cols-3 gap-2 text-xs text-zinc-600">
                          <div className="rounded-[1rem] border border-[var(--pv-border)] bg-white/78 px-3 py-3">
                            <p className="uppercase tracking-[0.08em] text-zinc-500"><T k="learn.modulesShort" /></p>
                            <p className="mt-2 text-lg font-semibold text-zinc-950">{course.module_count}</p>
                          </div>
                          <div className="rounded-[1rem] border border-[var(--pv-border)] bg-white/78 px-3 py-3">
                            <p className="uppercase tracking-[0.08em] text-zinc-500"><T k="learn.lessonsShort" /></p>
                            <p className="mt-2 text-lg font-semibold text-zinc-950">{course.lesson_count}</p>
                          </div>
                          <div className="rounded-[1rem] border border-[var(--pv-border)] bg-white/78 px-3 py-3">
                            <p className="uppercase tracking-[0.08em] text-zinc-500"><T k="learn.effortShort" /></p>
                            <p className="mt-2 text-lg font-semibold text-zinc-950">{course.estimated_minutes}m</p>
                          </div>
                        </div>

                        <div
                          className="pv-progress"
                          role="progressbar"
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={course.progress_percent}
                        >
                          <div className="pv-progress-fill" style={{ width: `${course.progress_percent}%` }} />
                        </div>

                        <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-600">
                          {course.badge_earned ? <span className="pv-chip-brand"><T k="learn.completed" /></span> : null}
                          <TokenAmount amount={`+${course.course_reward_lmn}`} compact showIcon={false} />
                        </div>

                        <div className="flex flex-wrap gap-3">
                          <Link href={destination} className="pv-button-primary !w-auto">
                            {ctaLabel}
                          </Link>
                          <Link href={appRoute.learnCourse(course.slug)} className="pv-button-secondary !w-auto">
                            <T k="learn.openCourse" />
                          </Link>
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        )}

        <section className="grid gap-4 lg:grid-cols-3">
          <article className="pv-card p-5 text-sm text-zinc-700">
            <p className="pv-kicker">01</p>
            <p className="mt-3 font-semibold text-zinc-950"><T k="learn.learningLoopTheory" /></p>
            <p className="mt-2 leading-relaxed"><T k="learn.learningSystemBody" /></p>
          </article>
          <article className="pv-card p-5 text-sm text-zinc-700">
            <p className="pv-kicker">02</p>
            <p className="mt-3 font-semibold text-zinc-950"><T k="learn.learningLoopPractice" /></p>
            <p className="mt-2 leading-relaxed"><T k="learn.pathStagesBody" /></p>
          </article>
          <article className="pv-card p-5 text-sm text-zinc-700">
            <p className="pv-kicker">03</p>
            <p className="mt-3 font-semibold text-zinc-950"><T k="learn.learningLoopFeedback" /></p>
            <p className="mt-2 leading-relaxed"><T k="learn.recommendedFocus" /></p>
          </article>
        </section>
      </div>
    );
  } catch (error) {
    const message =
      error instanceof ApiRequestError ? error.message : getTranslation(language, "learn.loadFailed");

    return (
      <div className="pv-page-sm">
        <div className="pv-alert pv-alert-warning">{message}</div>
      </div>
    );
  }
}

