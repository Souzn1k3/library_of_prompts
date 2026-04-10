"use client";

import { getTokenDisplayLabel, TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { LearningCourseDetail } from "@/lib/types";

import type {
  DashboardMissionHeroProps,
  DashboardMissionHeroViewModel,
} from "@/components/dashboard/hero/types";

type TranslateFn = (
  key: string,
  params?: Record<string, string | number | null | undefined>,
) => string;

export function useDashboardMissionHeroViewModel(
  {
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
  }: DashboardMissionHeroProps,
  t: TranslateFn,
): DashboardMissionHeroViewModel {
  const nextStepIsLearning = primaryAction.href.startsWith("/learn");
  const walletSymbol = TOKEN_SHORT_CODE;
  const walletBalanceLabel =
    typeof wallet?.balance === "number"
      ? `${wallet.balance} ${getTokenDisplayLabel(wallet.balance)}`
      : `— ${getTokenDisplayLabel(0)}`;
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
  const nextStepActionLabel = simplifyActionLabel(primaryAction.label);

  const promptsAction =
    rejectedSubmissionCount > 0
      ? { href: `${APP_ROUTES.dashboard}#submissions`, label: t("dashboard.opsFixSubmissions") }
      : savedPromptsCount === 0
        ? { href: APP_ROUTES.catalog, label: t("dashboard.opsSaveFirstPrompt") }
        : submissionCount === 0
          ? { href: APP_ROUTES.submit, label: t("dashboard.opsSendFirstPrompt") }
          : { href: `${APP_ROUTES.dashboard}#submissions`, label: t("dashboard.opsOpenSubmissions") };

  const promptsBody =
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

  return {
    nextStepTitle,
    nextStepBody,
    nextStepActionLabel,
    learningProgressPercent,
    learningSubline,
    learningBody,
    learningActionHref,
    learningActionLabel,
    learningEmptySummary,
    promptsActionHref: promptsAction.href,
    promptsActionLabel: promptsAction.label,
    promptsBody,
    walletBalanceLabel,
    walletBody,
  };
}

function simplifyActionLabel(label: string): string {
  const simplified = label.replace(/^[^:]+:\s*/, "").trim();
  return simplified || label;
}

function countCompletedLessons(course: LearningCourseDetail): number {
  return course.modules.reduce(
    (sum, module) => sum + module.lessons.filter((lesson) => lesson.status === "completed").length,
    0,
  );
}
