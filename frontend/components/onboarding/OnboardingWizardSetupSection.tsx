"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { OnboardingOptionStep } from "@/components/onboarding/OnboardingOptionStep";
import type { OnboardingOption } from "@/components/onboarding/options";
import type { OnboardingGoal, OnboardingRole } from "@/lib/types";

type OnboardingWizardSetupSectionProps = {
  step: number;
  role: OnboardingRole | null;
  goal: OnboardingGoal | null;
  aiContext: string | null;
  pending: boolean;
  roleOptions: OnboardingOption<OnboardingRole>[];
  goalOptions: OnboardingOption<OnboardingGoal>[];
  contextOptions: OnboardingOption[];
  selectRole: (value: OnboardingRole) => void;
  selectGoal: (value: OnboardingGoal) => void;
  selectAiContext: (value: string) => void;
  goBack: () => void;
  goNext: () => void;
  completeOnboardingFlow: () => Promise<void>;
};

export function OnboardingWizardSetupSection({
  step,
  role,
  goal,
  aiContext,
  pending,
  roleOptions,
  goalOptions,
  contextOptions,
  selectRole,
  selectGoal,
  selectAiContext,
  goBack,
  goNext,
  completeOnboardingFlow,
}: OnboardingWizardSetupSectionProps) {
  const { t } = useI18n();

  return (
    <div className="pv-hero space-y-5 px-5 py-5 sm:px-6">
      {step === 0 ? (
        <OnboardingOptionStep
          title={t("onboardingWizard.stepRoleTitle")}
          subtitle={t("onboardingWizard.stepRoleSubtitle")}
          options={roleOptions}
          selected={role}
          onSelect={(value) => selectRole(value as OnboardingRole)}
        />
      ) : null}
      {step === 1 ? (
        <OnboardingOptionStep
          title={t("onboardingWizard.stepGoalTitle")}
          subtitle={t("onboardingWizard.stepGoalSubtitle")}
          options={goalOptions}
          selected={goal}
          onSelect={(value) => selectGoal(value as OnboardingGoal)}
        />
      ) : null}
      {step === 2 ? (
        <OnboardingOptionStep
          title={t("onboardingWizard.stepContextTitle")}
          subtitle={t("onboardingWizard.stepContextSubtitle")}
          options={contextOptions}
          selected={aiContext}
          onSelect={selectAiContext}
        />
      ) : null}

      <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={goBack}
          disabled={step === 0 || pending}
          className="pv-button-secondary w-full sm:w-auto disabled:opacity-50"
        >
          {t("onboardingWizard.back")}
        </button>
        {step < 2 ? (
          <button
            type="button"
            onClick={goNext}
            disabled={pending || (step === 0 && !role) || (step === 1 && !goal)}
            className="pv-button-primary w-full sm:w-auto disabled:opacity-60"
          >
            {t("onboardingWizard.continue")}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void completeOnboardingFlow()}
            disabled={pending || !aiContext}
            className="pv-button-primary w-full sm:w-auto disabled:opacity-60"
          >
            {pending ? t("onboardingWizard.preparing") : t("onboardingWizard.finishSetup")}
          </button>
        )}
      </div>
    </div>
  );
}
