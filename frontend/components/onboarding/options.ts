"use client";

import type { TranslationKey } from "@/lib/i18n";
import type { OnboardingGoal, OnboardingRole } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

export type OnboardingOption<T extends string = string> = {
  value: T;
  label: string;
  hint: string;
};

export function getRoleOptions(t: Translate): OnboardingOption<OnboardingRole>[] {
  return [
    {
      value: "student",
      label: t("onboardingWizard.roleStudentLabel"),
      hint: t("onboardingWizard.roleStudentHint"),
    },
    {
      value: "developer",
      label: t("onboardingWizard.roleDeveloperLabel"),
      hint: t("onboardingWizard.roleDeveloperHint"),
    },
    {
      value: "other",
      label: t("onboardingWizard.roleOtherLabel"),
      hint: t("onboardingWizard.roleOtherHint"),
    },
  ];
}

export function getGoalOptions(t: Translate): OnboardingOption<OnboardingGoal>[] {
  return [
    {
      value: "learning",
      label: t("onboardingWizard.goalLearningLabel"),
      hint: t("onboardingWizard.goalLearningHint"),
    },
    {
      value: "solving_tasks",
      label: t("onboardingWizard.goalSolvingLabel"),
      hint: t("onboardingWizard.goalSolvingHint"),
    },
    {
      value: "productivity",
      label: t("onboardingWizard.goalProductivityLabel"),
      hint: t("onboardingWizard.goalProductivityHint"),
    },
  ];
}

export function getContextOptions(t: Translate): OnboardingOption[] {
  return [
    {
      value: "chatgpt",
      label: t("onboardingWizard.contextGeneralLabel"),
      hint: t("onboardingWizard.contextGeneralHint"),
    },
    {
      value: "code_assistant",
      label: t("onboardingWizard.contextCodeLabel"),
      hint: t("onboardingWizard.contextCodeHint"),
    },
    {
      value: "school",
      label: t("onboardingWizard.contextSchoolLabel"),
      hint: t("onboardingWizard.contextSchoolHint"),
    },
    {
      value: "work",
      label: t("onboardingWizard.contextWorkLabel"),
      hint: t("onboardingWizard.contextWorkHint"),
    },
  ];
}
