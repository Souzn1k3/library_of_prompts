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
      aside={(
        <div className="pv-card flex h-full min-h-[14rem] flex-col gap-5 p-5 sm:p-6">
          <div className="space-y-3">
            <p className="pv-kicker">{t("dashboard.opsNextStepLabel")}</p>
            <h2 className="text-[1.55rem] font-semibold tracking-[-0.05em] text-zinc-950 sm:text-[1.75rem]">
              {viewModel.nextStepTitle}
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">{viewModel.nextStepBody}</p>
          </div>

          <div className="mt-auto border-t border-[var(--pv-border)] pt-4">
            <Link href={props.primaryAction.href} className="pv-inline-link flex w-full justify-between">
              {props.primaryAction.label}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>
      )}
    >
      <div className="pv-dashboard-split">
        <DashboardOpsCard
          eyebrow={t("dashboard.opsLearningLabel")}
          summary={(
            viewModel.learningEmptySummary ? (
              <p className="text-[1.35rem] font-semibold tracking-[-0.04em] text-zinc-900">
                {t("dashboard.opsLearningStartShort")}
              </p>
            ) : (
              <div className="space-y-1">
                <p className="text-[clamp(2rem,4vw,2.8rem)] font-semibold tracking-[-0.08em] text-zinc-950">
                  {viewModel.learningProgressPercent}%
                </p>
                <p className="text-xs font-medium text-zinc-500">{viewModel.learningSubline}</p>
              </div>
            )
          )}
          body={viewModel.learningBody}
          href={viewModel.learningActionHref}
          actionLabel={viewModel.learningActionLabel}
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsPromptsAndSubmissionsLabel")}
          summary={(
            props.savedPromptsCount === 0 ? (
              <p className="text-[1.35rem] font-semibold tracking-[-0.04em] text-zinc-900">
                {t("dashboard.opsPromptsEmptyShort")}
              </p>
            ) : (
              <div className="space-y-2">
                <DashboardMiniMetric label={t("dashboard.opsMetricSaved")} value={props.savedPromptsCount} />
                <DashboardMiniMetric label={t("dashboard.opsMetricSubmitted")} value={props.submissionCount} />
                <DashboardMiniMetric label={t("dashboard.opsMetricNeedsFix")} value={props.rejectedSubmissionCount} />
              </div>
            )
          )}
          body={viewModel.promptsBody}
          href={viewModel.promptsActionHref}
          actionLabel={viewModel.promptsActionLabel}
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsWalletLabel")}
          summary={(
            <p className="text-[clamp(2rem,4vw,2.8rem)] font-semibold tracking-[-0.08em] text-zinc-950">
              {viewModel.walletBalanceLabel}
            </p>
          )}
          body={viewModel.walletBody}
          href={APP_ROUTES.wallet}
          actionLabel={t("dashboard.openWallet")}
        />
      </div>
    </PageIntro>
  );
}
