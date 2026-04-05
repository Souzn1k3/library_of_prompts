"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatMissionDateTime, type MissionPresentation } from "@/lib/missionPresentation";
import { getMissionStatusTranslationKey, type TranslationKey } from "@/lib/i18n";

type MissionDetailHeaderProps = {
  missionView: MissionPresentation;
  nextStep: MissionPresentation["nextStep"];
  onNextStepClick: () => void;
};

export function MissionDetailHeader({ missionView, nextStep, onNextStepClick }: MissionDetailHeaderProps) {
  const { t, language } = useI18n();
  const currentMission = missionView.mission;
  const pct = Math.round((currentMission.progress_count / Math.max(1, currentMission.required_count)) * 100);

  return (
    <PageIntro
      breadcrumbs={[
        { label: t("nav.missions"), href: APP_ROUTES.missions },
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
      actions={(
        <>
          {nextStep ? (
            <Link href={nextStep.href} onClick={onNextStepClick} className="pv-button-primary">
              {nextStep.label}
            </Link>
          ) : null}
          <Link href={APP_ROUTES.wallet} className="pv-button-secondary">
            {t("nav.wallet")}
          </Link>
          <Link href={APP_ROUTES.store} className="pv-inline-link">
            {t("nav.store")}
            <span aria-hidden="true">↗</span>
          </Link>
        </>
      )}
      aside={(
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
      )}
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
  );
}
