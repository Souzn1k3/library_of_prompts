"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import type { TranslationKey } from "@/lib/i18n";
import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { fetchMissionBySlug } from "@/lib/client-api";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { getMissionStatusTranslationKey } from "@/lib/i18n";
import {
  formatMissionDateTime,
  getMissionPresentation,
} from "@/lib/missionPresentation";
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
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          className="pv-button-secondary !w-auto"
        >
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  const missionView = mission ? getMissionPresentation(language, mission) : null;

  if (loading || !missionView) {
    return <p className="text-sm text-zinc-500">{t("missionDetail.loading")}</p>;
  }

  const currentMission = missionView.mission;
  const pct = Math.round((currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100);
  const nextStep =
    missionView.nextStep?.href === `/missions/${currentMission.slug}` ? null : missionView.nextStep;

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
      <PageIntro
        breadcrumbs={[
          { label: t("nav.missions"), href: "/missions" },
          { label: missionView.title },
        ]}
        eyebrow={t(`missions.type.${currentMission.mission_type}` as TranslationKey)}
        title={missionView.title}
        description={missionView.description ?? missionView.objective}
        hint={
          nextStep
            ? `${t("dashboard.recommendedNextAction")}: ${nextStep.label}`
            : t("missionDetail.completionCondition")
        }
        actions={
          <>
            {nextStep ? (
              <Link href={nextStep.href} onClick={trackNextStep} className="pv-button-primary">
                {nextStep.label}
              </Link>
            ) : null}
            <Link href="/wallet" className="pv-button-secondary">
              {t("nav.wallet")}
            </Link>
            <Link href="/store" className="pv-inline-link">
              {t("nav.store")}
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
        aside={
          <div className="grid gap-3">
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("missions.progress")}</p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">
                {currentMission.progress_count}/{currentMission.required_count}
              </p>
              <div className="mt-3 pv-progress">
                <div className="pv-progress-fill" style={{ width: `${pct}%` }} />
              </div>
              <div className="mt-4 space-y-2 text-sm text-zinc-600">
                {missionView.badgeLabel ? (
                  <p>
                    {t("missions.badge")}: {missionView.badgeLabel}
                  </p>
                ) : null}
                {currentMission.reward.premium_days ? (
                  <p>
                    {t("missions.premiumUnlockDays")}: {currentMission.reward.premium_days}
                  </p>
                ) : null}
                {currentMission.completion_count > 0 ? (
                  <p>
                    {t("missions.completedTimes")}: {currentMission.completion_count}
                  </p>
                ) : null}
                {currentMission.available_again_at ? (
                  <p>
                    {t("missions.availableAgain")}: {formatMissionDateTime(language, currentMission.available_again_at)}
                  </p>
                ) : null}
              </div>
            </div>
            {currentMission.reward.credits > 0 ? (
              <LmnBalanceCard
                label={t("missionDetail.reward")}
                amount={`+${currentMission.reward.credits}`}
                symbol={TOKEN_SHORT_CODE}
                caption={t("missions.credits")}
                tone="earned"
                showIcon
                compactCode={false}
              />
            ) : null}
          </div>
        }
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="pv-badge">
            {t(`missions.difficulty.${currentMission.difficulty}` as TranslationKey)}
          </span>
          <span className="pv-badge">
            {t(getMissionStatusTranslationKey(currentMission.status))}
          </span>
          {currentMission.is_repeatable ? <span className="pv-badge">{t("missions.repeatable")}</span> : null}
        </div>
        <p className="max-w-3xl text-sm text-zinc-800">
          <span className="font-medium">{t("missionDetail.objective")}:</span> {missionView.objective}
        </p>
        <p className="max-w-3xl text-sm text-zinc-600">
          {t("missionDetail.completionCondition")}: {missionView.completionCondition}
        </p>
      </PageIntro>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        {missionView.steps.length ? (
          <section className="pv-panel px-6 py-6 sm:px-7">
            <p className="pv-kicker">{t("missions.steps")}</p>
            <div className="mt-4 space-y-3">
              {missionView.steps.map((step, index) => (
                <div key={step.id} className="pv-card-muted p-4">
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
                      {step.reward_credits > 0 ? (
                        <LmnAmount amount={`+${step.reward_credits}`} symbol={TOKEN_SHORT_CODE} state="earned" />
                      ) : null}
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
            <p className="mt-4 text-sm leading-relaxed text-zinc-700">{missionView.objective}</p>
          </section>
        )}

        <aside className="space-y-4">
          {currentMission.prompts.length ? (
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">{t("missionDetail.linkedPrompts")}</p>
              <ul className="mt-4 space-y-3 text-sm text-zinc-700">
                {currentMission.prompts.map((prompt) => (
                  <li key={prompt.id} className="pv-card-muted p-3">
                    <Link href={`/prompt/${prompt.slug}`} className="font-medium text-zinc-900 underline">
                      {prompt.title}
                    </Link>
                    {prompt.summary ? <p className="mt-1 text-zinc-600">{prompt.summary}</p> : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {currentMission.lesson ? (
            <section className="pv-panel px-5 py-5">
              <p className="pv-kicker">{t("missionDetail.linkedLesson")}</p>
              <p className="mt-4 text-sm font-medium text-zinc-950">{currentMission.lesson.title}</p>
              <Link href={`/learn/${currentMission.lesson.slug}`} className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
                {currentMission.lesson.locked ? `${t("missionDetail.locked")} · ${t("nav.plans")}` : t("learn.open")}
                <span aria-hidden="true">↗</span>
              </Link>
            </section>
          ) : null}
        </aside>
      </div>
    </article>
  );
}
