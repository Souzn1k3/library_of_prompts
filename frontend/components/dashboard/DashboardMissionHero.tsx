"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import {
  DashboardMiniMetric,
  DashboardOpsCard,
} from "@/components/dashboard/hero/DashboardOpsCard";
import { useDashboardMissionHeroViewModel } from "@/components/dashboard/hero/useDashboardMissionHeroViewModel";
import type { DashboardMissionHeroProps } from "@/components/dashboard/hero/types";
import { APP_ROUTES } from "@/lib/constants/routes";

export function DashboardMissionHero(props: DashboardMissionHeroProps) {
  const { t } = useI18n();
  const viewModel = useDashboardMissionHeroViewModel(props, t);

  return (
    <PageIntro
      eyebrow={t("dashboard.title")}
      title={t("dashboard.title")}
      description={t("dashboard.subtitle")}
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-12">
        <div className="pv-card-muted pv-card-hover-lift flex h-full min-h-[12rem] flex-col gap-4 border-[rgba(37,92,255,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(237,244,255,0.92))] p-5 shadow-[0_18px_36px_rgba(37,92,255,0.08)] md:col-span-2 xl:col-span-6 sm:p-6">
          <p className="pv-kicker">{t("dashboard.opsNextStepLabel")}</p>
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-[-0.035em] text-zinc-950 sm:text-2xl">
              {viewModel.nextStepTitle}
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">{viewModel.nextStepBody}</p>
          </div>

          <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
            <Link href={props.primaryAction.href} className="pv-inline-link flex w-full justify-between">
              {props.primaryAction.label}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>

        <DashboardOpsCard
          eyebrow={t("dashboard.opsLearningLabel")}
          summary={(
            viewModel.learningEmptySummary ? (
              <p className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">
                {t("dashboard.opsLearningStartShort")}
              </p>
            ) : (
              <div className="space-y-1">
                <p className="text-[clamp(2rem,4vw,2.6rem)] font-extrabold tracking-[-0.08em] text-zinc-950">
                  {viewModel.learningProgressPercent}%
                </p>
                <p className="text-xs font-medium text-zinc-500">{viewModel.learningSubline}</p>
              </div>
            )
          )}
          body={viewModel.learningBody}
          href={viewModel.learningActionHref}
          actionLabel={viewModel.learningActionLabel}
          className="xl:col-span-2"
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsPromptsAndSubmissionsLabel")}
          summary={(
            props.savedPromptsCount === 0 ? (
              <p className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">
                {t("dashboard.opsPromptsEmptyShort")}
              </p>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                <DashboardMiniMetric label={t("dashboard.opsMetricSaved")} value={props.savedPromptsCount} />
                <DashboardMiniMetric label={t("dashboard.opsMetricSubmitted")} value={props.submissionCount} />
                <DashboardMiniMetric label={t("dashboard.opsMetricNeedsFix")} value={props.rejectedSubmissionCount} />
              </div>
            )
          )}
          body={viewModel.promptsBody}
          href={viewModel.promptsActionHref}
          actionLabel={viewModel.promptsActionLabel}
          className="xl:col-span-2"
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsWalletLabel")}
          summary={(
            <p className="text-[clamp(2rem,4vw,2.6rem)] font-extrabold tracking-[-0.08em] text-zinc-950">
              {viewModel.walletBalanceLabel}
            </p>
          )}
          body={viewModel.walletBody}
          href={APP_ROUTES.wallet}
          actionLabel={t("dashboard.openWallet")}
          className="xl:col-span-2"
        />
      </div>
    </PageIntro>
  );
}
