import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTranslation, languageToIntlLocale, type Language } from "@/lib/i18n";

import { ActiveCourseCard, CompletedCourseCard, WeakAreaCard } from "./MyLearningCards";
import { MyLearningGuestView } from "./MyLearningGuestView";
import type { MyLearningPageData } from "./my-learning-page-data";

type MyLearningModulesViewProps = {
  language: Language;
  data: MyLearningPageData;
};

export function MyLearningModulesView({ language, data }: MyLearningModulesViewProps) {
  if (data.mode === "guest") {
    return <MyLearningGuestView language={language} />;
  }

  const locale = languageToIntlLocale(language);
  const myModules = data.modules;

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
              <ActiveCourseCard key={course.slug} course={course} locale={locale} />
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
              <CompletedCourseCard key={course.slug} course={course} language={language} locale={locale} />
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
              <WeakAreaCard key={`${area.tag}-${area.lesson_slug ?? "none"}`} area={area} />
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
