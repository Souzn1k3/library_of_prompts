"use client";

import type { LearningCourseDetail, LearningMyModules, WalletRead } from "@/lib/types";
import type { MissionPresentation } from "@/lib/missionPresentation";

export type HeroAction = {
  href: string;
  label: string;
};

export type DashboardMissionHeroProps = {
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

export type DashboardMissionHeroViewModel = {
  nextStepTitle: string;
  nextStepBody: string;
  nextStepActionLabel: string;
  learningProgressPercent: number;
  learningSubline: string;
  learningBody: string;
  learningActionHref: string;
  learningActionLabel: string;
  learningEmptySummary: boolean;
  promptsActionHref: string;
  promptsActionLabel: string;
  promptsBody: string;
  walletBalanceLabel: string;
  walletBody: string;
};
