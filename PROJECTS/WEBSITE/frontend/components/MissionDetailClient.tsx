"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { TranslationKey } from "@/lib/i18n";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { fetchMissionBySlug } from "@/lib/client-api";
import { getMissionStatusTranslationKey } from "@/lib/i18n";
import type { MissionRead } from "@/lib/types";

export function MissionDetailClient({ slug }: { slug: string }) {
  const { t, language } = useI18n();
  const [mission, setMission] = useState<MissionRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetchMissionBySlug(slug)
      .then((row) => {
        setMission(row);
        setError(null);
      })
      .catch((e) => {
        setMission(null);
        if (e instanceof ApiRequestError && e.status === 401) {
          setError("signed_out");
        } else {
          setError(e instanceof Error ? e.message : t("missionDetail.loadFailed"));
        }
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug, language, reloadToken, t]);

  if (error === "signed_out") {
    return (
      <p className="text-sm text-zinc-600">
        {t("missionDetail.signInPrefix")}{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          {t("missionDetail.signInLink")}
        </Link>{" "}
        {t("missionDetail.signInSuffix")}
      </p>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  if (loading || !mission) {
    return <p className="text-sm text-zinc-500">{t("missionDetail.loading")}</p>;
  }

  const currentMission = mission;
  const pct = Math.round((currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100);
  const nextStep =
    currentMission.next_step?.href === `/missions/${currentMission.slug}` ? null : currentMission.next_step;

  function trackNextStep() {
    if (!nextStep) return;
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: `/missions/${currentMission.slug}`,
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

  return (
    <article className="space-y-5">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
                {t(`missions.type.${mission.mission_type}` as TranslationKey)}
              </span>
              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                {t(`missions.difficulty.${mission.difficulty}` as TranslationKey)}
              </span>
              <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                {t(getMissionStatusTranslationKey(mission.status))}
              </span>
              {mission.is_repeatable ? (
                <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-700">
                  {t("missions.repeatable")}
                </span>
              ) : null}
            </div>
            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-zinc-950">{mission.title}</h1>
            {mission.description ? <p className="max-w-3xl text-sm leading-relaxed text-zinc-600">{mission.description}</p> : null}
            <p className="max-w-3xl text-sm text-zinc-800">
              <span className="font-medium">{t("missionDetail.objective")}:</span> {mission.objective}
            </p>
            <p className="max-w-3xl text-sm text-zinc-600">
              {t("missionDetail.completionCondition")}: {mission.completion_condition}
            </p>
          </div>

          <div className="min-w-[240px] rounded-[1.25rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("missions.progress")}</p>
            <p className="mt-3 text-2xl font-semibold text-zinc-950">
              {mission.progress_count}/{mission.required_count}
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-200">
              <div className="h-full rounded-full bg-[var(--pv-brand)]" style={{ width: `${pct}%` }} />
            </div>
            <div className="mt-4 space-y-2 text-sm text-zinc-600">
              {mission.reward.credits > 0 ? (
                <p>
                  {t("missions.credits")}: +{mission.reward.credits}
                </p>
              ) : null}
              {mission.reward.badge ? (
                <p>
                  {t("missions.badge")}: {mission.reward.badge}
                </p>
              ) : null}
              {mission.reward.premium_days ? (
                <p>
                  {t("missions.premiumUnlockDays")}: {mission.reward.premium_days}
                </p>
              ) : null}
              {mission.completion_count > 0 ? (
                <p>
                  {t("missions.completedTimes")}: {mission.completion_count}
                </p>
              ) : null}
              {mission.available_again_at ? (
                <p>
                  {t("missions.availableAgain")}: {new Date(mission.available_again_at).toLocaleString()}
                </p>
              ) : null}
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          {nextStep ? (
            <Link
              href={nextStep.href}
              onClick={trackNextStep}
              className="inline-flex items-center rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-zinc-800"
            >
              {nextStep.label}
            </Link>
          ) : null}
          <Link href="/wallet" className="pv-button-secondary">
            {t("nav.wallet")}
          </Link>
          <Link href="/store" className="pv-button-secondary">
            {t("nav.store")}
          </Link>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        {mission.steps?.length ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <p className="pv-kicker">{t("missions.steps")}</p>
            <div className="mt-4 space-y-3">
              {mission.steps.map((step, index) => (
                <div key={step.id} className="rounded-[1.25rem] border border-[var(--pv-border)] bg-white/80 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                        {index + 1}. {t(getMissionStatusTranslationKey(step.status))}
                      </p>
                      <p className="text-base font-semibold text-zinc-950">{step.title}</p>
                      {step.description ? <p className="text-sm text-zinc-600">{step.description}</p> : null}
                    </div>
                    <div className="text-right text-sm text-zinc-600">
                      <p>
                        {step.progress_count}/{step.required_count}
                      </p>
                      {step.reward_credits > 0 ? <p>+{step.reward_credits} LMN</p> : null}
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-3">
                    {step.prompt ? (
                      <Link href={`/prompt/${step.prompt.slug}`} className="pv-inline-link">
                        {step.prompt.title}
                      </Link>
                    ) : null}
                    {step.lesson ? (
                      <Link href={`/learn/${step.lesson.slug}`} className="pv-inline-link">
                        {step.lesson.title}
                      </Link>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <p className="pv-kicker">{t("missions.objective")}</p>
            <p className="mt-4 text-sm leading-relaxed text-zinc-700">{mission.objective}</p>
          </section>
        )}

        <aside className="space-y-4">
          {mission.prompts.length ? (
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">{t("missionDetail.linkedPrompts")}</p>
              <ul className="mt-4 space-y-3 text-sm text-zinc-700">
                {mission.prompts.map((prompt) => (
                  <li key={prompt.id}>
                    <Link href={`/prompt/${prompt.slug}`} className="font-medium text-zinc-900 underline">
                      {prompt.title}
                    </Link>
                    {prompt.summary ? <p className="mt-1 text-zinc-600">{prompt.summary}</p> : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {mission.lesson ? (
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">{t("missionDetail.linkedLesson")}</p>
              <p className="mt-4 text-sm font-medium text-zinc-950">{mission.lesson.title}</p>
              <Link href={`/learn/${mission.lesson.slug}`} className="mt-3 inline-flex text-sm font-medium text-[var(--pv-brand)]">
                {mission.lesson.locked ? `${t("missionDetail.locked")} · ${t("nav.plans")}` : t("learn.open")}
              </Link>
            </section>
          ) : null}
        </aside>
      </div>
    </article>
  );
}
