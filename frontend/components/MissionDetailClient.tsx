"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { useMissionDetailData } from "@/components/missions/detail/useMissionDetailData";
import { trackEvent } from "@/lib/analytics";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatMissionDateTime, getMissionPresentation } from "@/lib/missionPresentation";
import type { MissionRead } from "@/lib/types";

type MissionDetailClientProps = {
  slug: string;
  initialMission?: MissionRead | null;
  initialError?: string | null;
  initialSignedOut?: boolean;
};

export function MissionDetailClient({
  slug,
  initialMission = null,
  initialError = null,
  initialSignedOut = false,
}: MissionDetailClientProps) {
  const { t, language } = useI18n();
  const { mission, error, isSignedOut, loading, retry } = useMissionDetailData({
    slug,
    language,
    loadFailedMessage: t("missionDetail.loadFailed"),
    initialMission,
    initialError,
    initialSignedOut,
  });

  const missionView = useMemo(
    () => (mission ? getMissionPresentation(language, mission) : null),
    [language, mission],
  );

  const currentMission = missionView?.mission ?? null;
  const nextStep = useMemo(() => {
    if (!missionView) {
      return null;
    }
    if (missionView.nextStep?.href === appRoute.missionBySlug(missionView.mission.slug)) {
      return null;
    }
    return missionView.nextStep;
  }, [missionView]);

  function trackNextStep() {
    if (!nextStep || !currentMission) {
      return;
    }
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: appRoute.missionBySlug(currentMission.slug),
      feature: "mission_detail",
      metadata: {
        mission_id: currentMission.id,
        mission_slug: currentMission.slug,
        status: currentMission.status,
        progress_count: currentMission.progress_count,
        required_count: currentMission.required_count,
        action: nextStep.action,
        href: nextStep.href,
      },
    });
  }

  if (isSignedOut) {
    return (
      <p className="text-sm text-zinc-600">
        {t("missionDetail.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("missionDetail.signInLink")}
        </Link>{" "}
        {t("missionDetail.signInSuffix")}
      </p>
    );
  }

  if (error) {
    return (
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{error}</p>
        <button type="button" onClick={retry} className="pv-button-secondary !w-auto">
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (loading || !missionView || !currentMission) {
    return <p className="text-sm text-zinc-500">{t("missionDetail.loading")}</p>;
  }

  const progress = Math.round(
    (currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100,
  );

  return (
    <article className="space-y-6">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)]">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="pv-chip-brand">{t(`missions.type.${currentMission.mission_type}`)}</span>
              <span className="pv-chip">{t(`missions.status.${currentMission.status}`)}</span>
              {currentMission.is_repeatable ? <span className="pv-chip">{t("missions.repeatable")}</span> : null}
            </div>
            <h1 className="text-4xl font-semibold tracking-[-0.06em] text-zinc-950 sm:text-5xl">
              {missionView.title}
            </h1>
            <p className="pv-lead">{missionView.objective}</p>

            <div className="pv-cta-group">
              {nextStep ? (
                <Link href={nextStep.href} onClick={trackNextStep} className="pv-button-primary !w-auto">
                  {nextStep.label}
                </Link>
              ) : null}
              <Link href={APP_ROUTES.missions} className="pv-button-secondary !w-auto">
                {t("missions.title")}
              </Link>
            </div>
          </div>

          <div className="grid gap-3">
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missionDetail.progress")}</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-zinc-950">
                {currentMission.progress_count}/{currentMission.required_count}
              </p>
              <div className="mt-3 pv-progress">
                <div className="pv-progress-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{t("missionDetail.reward")}</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-zinc-950">
                +{currentMission.reward.credits}
              </p>
            </div>
            <div className="rounded-[1.35rem] border border-[var(--pv-border)] bg-white/78 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("missionDetail.completionCondition")}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-zinc-700">{missionView.completionCondition}</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <section className="pv-panel px-6 py-6 sm:px-7">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("missions.steps")}</p>
              <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">{missionView.title}</h2>
            </div>
          </div>

          <ol className="mt-5 grid gap-3">
            {missionView.steps.map((step, index) => {
              const stepProgress = Math.round((step.progress_count / Math.max(1, step.required_count)) * 100);

              return (
                <li
                  key={step.id}
                  className={`rounded-[1.35rem] border px-4 py-4 ${
                    step.status === "completed"
                      ? "border-emerald-200 bg-emerald-50/70"
                      : "border-[var(--pv-border)] bg-white/78"
                  }`}
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                        0{index + 1}
                      </p>
                      <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{step.title}</p>
                      {step.description ? (
                        <p className="text-sm leading-relaxed text-zinc-600">{step.description}</p>
                      ) : null}
                    </div>
                    <div className="min-w-[8rem] text-sm text-zinc-600">
                      {step.progress_count}/{step.required_count}
                    </div>
                  </div>
                  <div className="mt-3 pv-progress">
                    <div className="pv-progress-fill" style={{ width: `${stepProgress}%` }} />
                  </div>
                </li>
              );
            })}
          </ol>
        </section>

        <aside className="space-y-4">
          <section className="pv-panel px-5 py-5">
            <p className="text-sm font-semibold text-zinc-950">{t("missionDetail.linkedPrompts")}</p>
            <div className="mt-3 grid gap-2">
              {currentMission.prompts.length ? (
                currentMission.prompts.map((prompt) => (
                  <Link
                    key={prompt.id}
                    href={appRoute.promptBySlug(prompt.slug)}
                    className="rounded-[1.15rem] border border-[var(--pv-border)] bg-white/78 px-3 py-3 text-sm text-zinc-700 transition hover:border-[var(--pv-border-strong)]"
                  >
                    <p className="font-medium text-zinc-950">{prompt.title}</p>
                    {prompt.summary ? <p className="mt-1 text-xs text-zinc-600">{prompt.summary}</p> : null}
                  </Link>
                ))
              ) : (
                <p className="text-sm text-zinc-500">{t("missions.subtitle")}</p>
              )}
            </div>
          </section>

          <section className="pv-panel px-5 py-5">
            <p className="text-sm font-semibold text-zinc-950">{t("missionDetail.linkedLesson")}</p>
            {currentMission.lesson ? (
              <Link
                href={appRoute.learnBySlug(currentMission.lesson.slug)}
                className="mt-3 block rounded-[1.15rem] border border-[var(--pv-border)] bg-white/78 px-3 py-3 text-sm text-zinc-700 transition hover:border-[var(--pv-border-strong)]"
              >
                <p className="font-medium text-zinc-950">{currentMission.lesson.title}</p>
                <p className="mt-1 text-xs text-zinc-600">
                  {currentMission.lesson.locked ? t("missionDetail.locked") : t("missions.openMission")}
                </p>
              </Link>
            ) : (
              <p className="mt-3 text-sm text-zinc-500">{t("missions.subtitle")}</p>
            )}
          </section>

          {currentMission.available_again_at ? (
            <section className="pv-panel px-5 py-5 text-sm text-zinc-700">
              {t("missions.availableAgain")}: {formatMissionDateTime(language, currentMission.available_again_at)}
            </section>
          ) : null}
        </aside>
      </div>
    </article>
  );
}
