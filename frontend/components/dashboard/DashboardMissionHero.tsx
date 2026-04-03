"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import type { MissionPresentation } from "@/lib/missionPresentation";
import type { LearningCourseDetail, LearningMyModules, WalletRead } from "@/lib/types";

type HeroAction = {
  href: string;
  label: string;
};

type DashboardMissionHeroProps = {
  currentMission: MissionPresentation | null;
  needsOnboarding: boolean;
  primaryAction: HeroAction;
  learningOverviewHref: string;
  missionCompletedCount: number;
  missionTotalCount: number;
  savedPromptsCount: number;
  submissionCount: number;
  rejectedSubmissionCount: number;
  pendingSubmissionCount: number;
  wallet: WalletRead | null;
  balanceDelta: number | null;
  learningMy: LearningMyModules | null;
  learningCourse: LearningCourseDetail | null;
  lessonHref: string;
};

export function DashboardMissionHero({
  currentMission,
  needsOnboarding,
  primaryAction,
  learningOverviewHref,
  missionCompletedCount,
  missionTotalCount,
  savedPromptsCount,
  submissionCount,
  rejectedSubmissionCount,
  pendingSubmissionCount,
  wallet,
  balanceDelta,
  learningMy,
  learningCourse,
  lessonHref,
}: DashboardMissionHeroProps) {
  const { t } = useI18n();
  const nextStepIsLearning = primaryAction.href.startsWith("/learn");
  const walletSymbol = wallet?.currency_symbol ?? "LMN";
  const walletBalanceLabel =
    typeof wallet?.balance === "number" ? `${wallet.balance} ${walletSymbol}` : `— ${walletSymbol}`;
  const pendingRewardAmount = (wallet?.pending_locked_rewards ?? [])
    .filter((reward) => reward.status === "pending")
    .reduce((sum, reward) => sum + reward.amount, 0);
  const balanceDeltaLabel = balanceDelta
    ? `${balanceDelta > 0 ? "+" : ""}${balanceDelta} ${walletSymbol}`
    : null;

  const activeCourse = learningMy?.active_courses[0] ?? null;
  const completedCoursesCount = learningMy?.completed_courses.length ?? 0;
  const totalCoursesCount = completedCoursesCount + (learningMy?.active_courses.length ?? 0);
  const completedLessons = learningCourse ? countCompletedLessons(learningCourse) : null;
  const totalLessons = learningCourse?.lesson_count ?? null;
  const missionProgressPercent =
    missionTotalCount > 0 ? Math.round((missionCompletedCount / missionTotalCount) * 100) : 0;
  const learningProgressPercent = Math.max(
    0,
    Math.min(
      100,
      activeCourse?.progress_percent ??
        learningCourse?.progress_percent ??
        (completedCoursesCount > 0 ? 100 : missionProgressPercent),
    ),
  );
  const remainingLessons =
    totalLessons !== null && completedLessons !== null
      ? Math.max(totalLessons - completedLessons, 0)
      : null;
  const learningHref = activeCourse?.continue_href ?? lessonHref;
  const learningActionHref = nextStepIsLearning ? learningOverviewHref : learningHref;
  const learningActionLabel = nextStepIsLearning
    ? t("dashboard.opsOpenLearningPlan")
    : activeCourse?.continue_href
      ? t("dashboard.opsContinueLearning")
      : t("dashboard.opsOpenModule");

  const nextStepTitle = needsOnboarding
    ? t("dashboard.opsNextStepOnboardingTitle")
    : currentMission?.title ?? t("dashboard.opsNextStepFallbackTitle");
  const nextStepBody = needsOnboarding
    ? t("dashboard.opsNextStepOnboardingBody")
    : currentMission
      ? t("dashboard.opsNextStepMissionBody", {
          progress: currentMission.mission.progress_count,
          required: currentMission.mission.required_count,
        })
      : t("dashboard.opsNextStepFallbackBody");

  const promptWorkflowAction =
    rejectedSubmissionCount > 0
      ? { href: "/dashboard#submissions", label: t("dashboard.opsFixSubmissions") }
      : savedPromptsCount === 0
        ? { href: "/catalog", label: t("dashboard.opsSaveFirstPrompt") }
        : submissionCount === 0
          ? { href: "/submit", label: t("dashboard.opsSendFirstPrompt") }
          : { href: "/dashboard#submissions", label: t("dashboard.opsOpenSubmissions") };

  const promptWorkflowBody =
    savedPromptsCount === 0
      ? t("dashboard.opsPromptsEmpty")
      : rejectedSubmissionCount > 0
        ? t("dashboard.opsPromptsNeedFix", {
            saved: savedPromptsCount,
            rejected: rejectedSubmissionCount,
          })
        : t("dashboard.opsPromptsFlow", {
            saved: savedPromptsCount,
            submitted: submissionCount,
            pending: pendingSubmissionCount,
          });

  const learningBody = !activeCourse && completedCoursesCount === 0 && !learningCourse
    ? needsOnboarding
      ? t("dashboard.opsLearningEmptyOnboarding")
      : t("dashboard.opsLearningEmpty")
    : remainingLessons !== null
      ? remainingLessons > 0
        ? t("dashboard.opsLearningRemaining", { count: remainingLessons })
        : t("dashboard.opsLearningCompletedHint")
      : activeCourse?.next_lesson_title
        ? t("dashboard.opsLearningNextLesson", { title: activeCourse.next_lesson_title })
        : activeCourse
          ? t("dashboard.opsLearningCourseFocus", { title: activeCourse.title })
          : missionTotalCount > 0
            ? t("dashboard.opsLearningMissionFallback", {
                percent: missionProgressPercent,
                completed: missionCompletedCount,
                total: missionTotalCount,
              })
            : t("dashboard.opsLearningEmpty");

  const learningSubline = totalLessons && completedLessons !== null
    ? t("dashboard.opsLearningLessons", {
        completed: completedLessons,
        total: totalLessons,
      })
    : totalCoursesCount > 0
      ? t("dashboard.opsLearningCourses", {
          completed: completedCoursesCount,
          total: totalCoursesCount,
        })
      : t("dashboard.opsLearningCoursesNone");
  const learningEmptySummary =
    !activeCourse &&
    completedCoursesCount === 0 &&
    !learningCourse &&
    missionProgressPercent === 0;

  const walletBody = pendingRewardAmount > 0
    ? t("dashboard.opsWalletPending", {
        amount: pendingRewardAmount,
        symbol: walletSymbol,
      })
    : balanceDeltaLabel
      ? t("dashboard.opsWalletDelta", {
          delta: balanceDeltaLabel,
        })
      : t("dashboard.walletSummaryBody");

  return (
    <PageIntro
      eyebrow={t("dashboard.title")}
      title={t("dashboard.title")}
      description={t("dashboard.subtitle")}
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-12">
        <div className="pv-card-muted flex h-full min-h-[12rem] flex-col gap-4 border-[rgba(37,92,255,0.14)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(237,244,255,0.92))] p-5 shadow-[0_18px_36px_rgba(37,92,255,0.08)] md:col-span-2 xl:col-span-6 sm:p-6">
          <p className="pv-kicker">{t("dashboard.opsNextStepLabel")}</p>
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-[-0.035em] text-zinc-950 sm:text-2xl">
              {nextStepTitle}
            </h2>
            <p className="text-sm leading-relaxed text-zinc-600">{nextStepBody}</p>
          </div>

          <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
            <Link href={primaryAction.href} className="pv-inline-link flex w-full justify-between">
              {primaryAction.label}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>

        <DashboardOpsCard
          eyebrow={t("dashboard.opsLearningLabel")}
          summary={(
            learningEmptySummary ? (
              <p className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">
                {t("dashboard.opsLearningStartShort")}
              </p>
            ) : (
              <div className="space-y-1">
                <p className="text-[clamp(2rem,4vw,2.6rem)] font-extrabold tracking-[-0.08em] text-zinc-950">
                  {learningProgressPercent}%
                </p>
                <p className="text-xs font-medium text-zinc-500">{learningSubline}</p>
              </div>
            )
          )}
          body={learningBody}
          href={learningActionHref}
          actionLabel={learningActionLabel}
          className="xl:col-span-2"
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsPromptsAndSubmissionsLabel")}
          summary={(
            savedPromptsCount === 0 ? (
              <p className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">
                {t("dashboard.opsPromptsEmptyShort")}
              </p>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                <MiniMetric label={t("dashboard.opsMetricSaved")} value={savedPromptsCount} />
                <MiniMetric label={t("dashboard.opsMetricSubmitted")} value={submissionCount} />
                <MiniMetric label={t("dashboard.opsMetricNeedsFix")} value={rejectedSubmissionCount} />
              </div>
            )
          )}
          body={promptWorkflowBody}
          href={promptWorkflowAction.href}
          actionLabel={promptWorkflowAction.label}
          className="xl:col-span-2"
        />

        <DashboardOpsCard
          eyebrow={t("dashboard.opsWalletLabel")}
          summary={(
            <p className="text-[clamp(2rem,4vw,2.6rem)] font-extrabold tracking-[-0.08em] text-zinc-950">
              {walletBalanceLabel}
            </p>
          )}
          body={walletBody}
          href="/wallet"
          actionLabel={t("dashboard.openWallet")}
          className="xl:col-span-2"
        />
      </div>
    </PageIntro>
  );
}

function DashboardOpsCard({
  eyebrow,
  summary,
  body,
  href,
  actionLabel,
  className,
}: {
  eyebrow: string;
  summary: ReactNode;
  body: string;
  href: string;
  actionLabel: string;
  className?: string;
}) {
  return (
    <div className={`pv-card-muted flex h-full min-h-[12rem] flex-col gap-3 p-4 sm:p-5 ${className ?? ""}`}>
      <p className="pv-kicker">{eyebrow}</p>
      <div className="space-y-2">
        {summary}
        <p className="line-clamp-2 text-sm leading-relaxed text-zinc-600">{body}</p>
      </div>
      <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-3">
        <Link href={href} className="pv-inline-link flex w-full justify-between">
          {actionLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-[rgba(15,23,42,0.08)] bg-white/80 px-2.5 py-2">
      <p className="text-lg font-bold tracking-[-0.04em] text-zinc-950">{value}</p>
      <p className="mt-0.5 text-[0.68rem] font-medium uppercase tracking-[0.13em] text-zinc-500">{label}</p>
    </div>
  );
}

function countCompletedLessons(course: LearningCourseDetail): number {
  return course.modules.reduce(
    (sum, module) => sum + module.lessons.filter((lesson) => lesson.status === "completed").length,
    0,
  );
}
