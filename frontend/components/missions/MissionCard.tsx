"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { trackEvent } from "@/lib/analytics";
import { MISSION_TYPE_TONE } from "@/lib/constants/economy-ui";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { getMissionStatusTranslationKey, type TranslationKey } from "@/lib/i18n";
import {
  formatMissionDateTime,
  type MissionPresentation,
} from "@/lib/missionPresentation";

type MissionCardProps = {
  mission: MissionPresentation;
};

export function MissionCard({ mission }: MissionCardProps) {
  const { t, language } = useI18n();
  const pct = Math.round(
    (mission.mission.progress_count / Math.max(1, mission.mission.required_count)) * 100,
  );
  const tone = MISSION_TYPE_TONE[mission.mission.mission_type];
  const detailsHref = appRoute.missionBySlug(mission.mission.slug);
  const hasDedicatedNextStep = Boolean(
    mission.nextStep && mission.nextStep.href && mission.nextStep.href !== detailsHref,
  );
  const primaryHref = hasDedicatedNextStep ? mission.nextStep!.href : detailsHref;
  const primaryLabel = hasDedicatedNextStep ? mission.nextStep!.label : t("missions.openMissionDetails");

  function trackNextStep() {
    if (!mission.nextStep || !hasDedicatedNextStep) return;
    trackEvent({
      eventName: "mission_next_step_clicked",
      page: APP_ROUTES.missions,
      feature: "mission_loop",
      metadata: {
        mission_id: mission.mission.id,
        mission_slug: mission.mission.slug,
        status: mission.mission.status,
        progress_count: mission.mission.progress_count,
        required_count: mission.mission.required_count,
        action: mission.nextStep.action,
        href: mission.nextStep.href,
      },
    });
  }

  return (
    <article className="pv-card pv-card-optimized p-5">
      <div className={`pointer-events-none absolute right-3 top-3 h-16 w-16 rounded-full blur-2xl ${tone.glow}`} />
      <div className="relative flex h-full flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${tone.badge}`}>
                {t(`missions.type.${mission.mission.mission_type}` as TranslationKey)}
              </span>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  mission.mission.status === "completed"
                    ? "bg-emerald-100 text-emerald-900"
                    : mission.mission.status === "in_progress"
                      ? "bg-blue-100 text-blue-900"
                      : "bg-zinc-100 text-zinc-700"
                }`}
              >
                {t(getMissionStatusTranslationKey(mission.mission.status))}
              </span>
              {mission.mission.is_repeatable ? (
                <span className="pv-badge">{t("missions.repeatable")}</span>
              ) : null}
              {mission.mission.chain_id ? (
                <span className="pv-badge">
                  {t("missions.chainProgress", {
                    step: mission.mission.chain_step,
                    total: mission.mission.chain_total || 1,
                  })}
                </span>
              ) : null}
            </div>
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{mission.title}</h3>
            <p className="text-sm leading-relaxed text-zinc-600">{mission.objective}</p>
          </div>

          {mission.mission.reward.credits > 0 ? (
            <LmnAmount
              amount={`+${mission.mission.reward.credits}`}
              symbol={TOKEN_SHORT_CODE}
              state="earned"
              strong
              compact
              className="shrink-0"
            />
          ) : null}
        </div>

        <div className="rounded-[1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] px-3 py-3">
          <div className="flex items-center justify-between text-xs text-zinc-600">
            <span>
              {t("missions.progress")}: {mission.mission.progress_count}/{mission.mission.required_count}
            </span>
            <span className="font-semibold text-zinc-700">{pct}%</span>
          </div>
          <div className="mt-2 pv-progress">
            <div className="pv-progress-fill" style={{ width: `${pct}%` }} />
          </div>
        </div>

        <div className="flex flex-wrap gap-3 text-xs text-zinc-500">
          {mission.badgeLabel ? (
            <span className="pv-chip">
              {t("missions.badge")}: {mission.badgeLabel}
            </span>
          ) : null}
          {mission.mission.completion_count > 0 ? (
            <span className="pv-chip">
              {t("missions.completedTimes")}: {mission.mission.completion_count}
            </span>
          ) : null}
          {mission.mission.adaptive_reason ? (
            <span className="pv-chip">
              {t("missions.adaptiveReason", { reason: mission.mission.adaptive_reason })}
            </span>
          ) : null}
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-3 border-t border-[var(--pv-border)] pt-4">
          <Link href={primaryHref} onClick={trackNextStep} className="pv-button-primary !w-auto">
            {primaryLabel}
          </Link>
          {hasDedicatedNextStep ? (
            <Link href={detailsHref} className="pv-inline-link">
              {t("missions.openMissionDetails")}
              <span aria-hidden="true">↗</span>
            </Link>
          ) : null}
        </div>

        {mission.mission.available_again_at ? (
          <p className="text-xs text-zinc-500">
            {t("missions.availableAgain")}: {formatMissionDateTime(language, mission.mission.available_again_at)}
          </p>
        ) : null}
      </div>
    </article>
  );
}
