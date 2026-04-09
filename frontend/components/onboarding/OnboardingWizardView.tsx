"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { OnboardingWizardHeader } from "@/components/onboarding/OnboardingWizardHeader";
import type { OnboardingOption } from "@/components/onboarding/options";
import { OnboardingWizardReadySection } from "@/components/onboarding/OnboardingWizardReadySection";
import { OnboardingWizardSetupSection } from "@/components/onboarding/OnboardingWizardSetupSection";
import { APP_ROUTES } from "@/lib/constants/routes";
import type {
  EconomyAction,
  OnboardingGoal,
  OnboardingRole,
  OnboardingStarterPack,
} from "@/lib/types";

type OnboardingWizardViewProps = {
  status: AuthStatus;
  loading: boolean;
  starter: OnboardingStarterPack | null;
  error: string | null;
  loadError: string | null;
  step: number;
  role: OnboardingRole | null;
  goal: OnboardingGoal | null;
  aiContext: string | null;
  pending: boolean;
  skipPending: boolean;
  firstWinDone: boolean;
  firstWinPending: boolean;
  firstWinEconomy: EconomyAction | null;
  roleOptions: OnboardingOption<OnboardingRole>[];
  goalOptions: OnboardingOption<OnboardingGoal>[];
  contextOptions: OnboardingOption[];
  progress: number;
  needsWizard: boolean;
  retryLoad: () => void;
  selectRole: (value: OnboardingRole) => void;
  selectGoal: (value: OnboardingGoal) => void;
  selectAiContext: (value: string) => void;
  goBack: () => void;
  goNext: () => void;
  completeOnboardingFlow: () => Promise<void>;
  skipFlow: () => Promise<void>;
  completeFirstWin: () => Promise<void>;
};

export function OnboardingWizardView({
  status,
  loading,
  starter,
  error,
  loadError,
  step,
  role,
  goal,
  aiContext,
  pending,
  skipPending,
  firstWinDone,
  firstWinPending,
  firstWinEconomy,
  roleOptions,
  goalOptions,
  contextOptions,
  progress,
  needsWizard,
  retryLoad,
  selectRole,
  selectGoal,
  selectAiContext,
  goBack,
  goNext,
  completeOnboardingFlow,
  skipFlow,
  completeFirstWin,
}: OnboardingWizardViewProps) {
  const { t } = useI18n();

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <div className="pv-empty-state text-sm text-zinc-600">
        {t("onboardingWizard.signInPrefix")}{" "}
        <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
          {t("onboardingWizard.signInLink")}
        </Link>{" "}
        {t("onboardingWizard.signInSuffix")}
      </div>
    );
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">{t("onboardingWizard.loading")}</p>;
  }

  if (loadError) {
    return (
      <div className="pv-alert pv-alert-warning space-y-3">
        <p>{loadError}</p>
        <button type="button" onClick={retryLoad} className="pv-button-secondary !w-auto">
          {t("dashboard.retry")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <OnboardingWizardHeader
        needsWizard={needsWizard}
        progress={progress}
        skipPending={skipPending}
        onSkip={skipFlow}
      />

      {needsWizard && step < 3 ? (
        <OnboardingWizardSetupSection
          step={step}
          role={role}
          goal={goal}
          aiContext={aiContext}
          pending={pending}
          roleOptions={roleOptions}
          goalOptions={goalOptions}
          contextOptions={contextOptions}
          selectRole={selectRole}
          selectGoal={selectGoal}
          selectAiContext={selectAiContext}
          goBack={goBack}
          goNext={goNext}
          completeOnboardingFlow={completeOnboardingFlow}
        />
      ) : null}

      {!needsWizard || step >= 3 ? (
        <OnboardingWizardReadySection
          starter={starter}
          firstWinDone={firstWinDone}
          firstWinPending={firstWinPending}
          firstWinEconomy={firstWinEconomy}
          completeFirstWin={completeFirstWin}
        />
      ) : null}

      {error ? <div className="pv-alert pv-alert-error">{error}</div> : null}
    </div>
  );
}
