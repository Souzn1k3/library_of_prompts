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

  function trackNextStep() {
    if (!mission.nextStep) return;
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
    <article className="pv-card p-5">
      <div className={`pointer-events-none absolute right-4 top-4 h-20 w-20 rounded-full blur-2xl ${tone.glow}`} />
      <div className="relative flex h-full flex-col gap-5">
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
            {mission.mission.adaptive_reason ? (
              <p className="text-xs text-zinc-500">
                {t("missions.adaptiveReason", { reason: mission.mission.adaptive_reason })}
              </p>
            ) : null}
          </div>

          {mission.mission.reward.credits > 0 ? (
            <LmnAmount amount={`+${mission.mission.reward.credits}`} symbol={TOKEN_SHORT_CODE} state="earned" strong />
          ) : null}
        </div>

        <div className="pv-progress">
          <div className="pv-progress-fill" style={{ width: `${pct}%` }} />
        </div>

        <div className="flex flex-wrap gap-3 text-xs text-zinc-500">
          <span>
            {t("missions.progress")}: {mission.mission.progress_count}/{mission.mission.required_count}
          </span>
          {mission.badgeLabel ? (
            <span>
              {t("missions.badge")}: {mission.badgeLabel}
            </span>
          ) : null}
          {mission.mission.completion_count > 0 ? (
            <span>
              {t("missions.completedTimes")}: {mission.mission.completion_count}
            </span>
          ) : null}
        </div>

        <div className="mt-auto flex flex-wrap gap-2">
          {mission.nextStep ? (
            <Link href={mission.nextStep.href} onClick={trackNextStep} className="pv-button-primary">
              {mission.nextStep.label}
            </Link>
          ) : null}
          <Link href={appRoute.missionBySlug(mission.mission.slug)} className="pv-button-secondary">
            {t("missions.openMissionDetails")}
          </Link>
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
