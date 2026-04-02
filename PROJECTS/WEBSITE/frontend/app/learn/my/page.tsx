import type { Metadata } from "next";
import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { ApiRequestError, fetchLearningMyModules } from "@/lib/api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { getTranslation, languageToIntlLocale, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export const revalidate = 0;

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return buildPageMetadata({
    title: `${getTranslation(language, "nav.learn")} · ${getTranslation(language, "learn.myModules")}`,
    description: getTranslation(language, "learn.myModulesDescription"),
    path: APP_ROUTES.learnMy,
  });
}

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

export default async function MyLearningModulesPage() {
  const language = await getServerLanguage();
  const locale = languageToIntlLocale(language);
  const accessToken = await getServerAccessToken();

  if (!accessToken) {
    return (
      <div className="pv-page-sm">
        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
            { label: getTranslation(language, "nav.learn"), href: APP_ROUTES.learn },
            { label: getTranslation(language, "learn.myModules") },
          ]}
          eyebrow={<T k="learn.myModules" />}
          title={<T k="learn.signInTitle" />}
          description={<T k="learn.signInDescription" />}
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                <T k="nav.login" />
              </Link>
              <Link href={APP_ROUTES.learn} className="pv-button-secondary">
                <T k="learn.viewCatalog" />
              </Link>
            </>
          }
        />
      </div>
    );
  }

  try {
    const myModules = await fetchLearningMyModules(accessToken, language);

    return (
      <div className="pv-page">
        <PageIntro
          breadcrumbs={[
            { label: getTranslation(language, "brand.name"), href: APP_ROUTES.home },
            { label: getTranslation(language, "nav.learn"), href: APP_ROUTES.learn },
            { label: getTranslation(language, "learn.myModules") },
          ]}
          eyebrow={<T k="learn.myModules" />}
          title={<T k="learn.myModules" />}
          description={<T k="learn.myModulesDescription" />}
          actions={
            <>
              <Link href={APP_ROUTES.learnStart} className="pv-button-primary">
                <T k="home.startLearning" />
              </Link>
              <Link href={APP_ROUTES.learn} className="pv-button-secondary">
                <T k="learn.viewCatalog" />
              </Link>
            </>
          }
        />

        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                <T k="learn.activeCourses" />
              </h2>
            </div>
          </div>

          {myModules.active_courses.length === 0 ? (
            <p className="mt-6 text-sm text-zinc-600">
              <T k="learn.noActiveCourses" />
            </p>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {myModules.active_courses.map((course) => (
                <article key={course.slug} className="pv-card p-5">
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
                      <dt><T k="learn.lastActivity" /></dt>
                      <dd>{formatDate(course.last_activity_at, locale)}</dd>
                    </div>
                    <div className="flex items-center justify-between gap-3">
                      <dt><T k="learn.nextLesson" /></dt>
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
              ))}
            </div>
          )}
        </section>

        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                <T k="learn.completedCourses" />
              </h2>
            </div>
          </div>

          {myModules.completed_courses.length === 0 ? (
            <p className="mt-6 text-sm text-zinc-600">
              <T k="learn.noCompletedCourses" />
            </p>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {myModules.completed_courses.map((course) => (
                <article key={course.slug} className="pv-card p-5">
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
                    {course.certificate_ready ? <span className="pv-chip-brand"><T k="learn.certificateReady" /></span> : null}
                  </div>

                  <div className="mt-4 flex gap-3">
                    <Link href={appRoute.learnCourse(course.slug)} className="pv-button-secondary !w-auto">
                      <T k="learn.reviewCourse" />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {myModules.weak_areas.length > 0 ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <div className="pv-section-head">
              <div className="pv-section-copy">
                <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
                  <T k="learn.recommendedFocus" />
                </h2>
              </div>
            </div>

            <ul className="mt-6 grid gap-3 lg:grid-cols-2">
              {myModules.weak_areas.map((area) => (
                <li key={`${area.tag}-${area.lesson_slug ?? "none"}`} className="pv-card p-4">
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
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    );
  } catch (error) {
    const message =
      error instanceof ApiRequestError ? error.message : getTranslation(language, "learn.loadFailed");
    return <div className="pv-page-sm"><div className="pv-alert pv-alert-warning">{message}</div></div>;
  }
}
