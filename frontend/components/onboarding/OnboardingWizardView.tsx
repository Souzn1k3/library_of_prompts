"use client";

import Link from "next/link";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
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
  const steps = [
    t("onboardingWizard.stepRoleTitle"),
    t("onboardingWizard.stepGoalTitle"),
    t("onboardingWizard.stepContextTitle"),
  ];

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
    <div className="grid gap-6 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <aside className="pv-panel space-y-5 px-5 py-5 sm:px-6">
        <div className="space-y-3">
          <p className="pv-kicker">{t("onboardingWizard.activationSetup")}</p>
          <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
            {needsWizard ? t("onboarding.pageTitle") : t("dashboard.finishOnboardingTitle")}
          </h2>
          <p className="text-sm leading-relaxed text-zinc-600">
            {needsWizard ? t("onboarding.pageSubtitle") : t("onboardingWizard.readyBody")}
          </p>
        </div>

        <div className="space-y-2">
          {steps.map((label, index) => {
            const isActive = needsWizard && index === step;
            const isDone = !needsWizard || index < progress;

            return (
              <div
                key={label}
                className={`rounded-[1.2rem] border px-4 py-3 transition ${
                  isActive
                    ? "border-[var(--pv-brand)]/30 bg-[var(--pv-brand-soft)]/65"
                    : isDone
                      ? "border-emerald-200 bg-emerald-50/70"
                      : "border-[var(--pv-border)] bg-white/65"
                }`}
              >
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">0{index + 1}</p>
                <p className="mt-2 text-sm font-semibold text-zinc-950">{label}</p>
              </div>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => void skipFlow()}
          disabled={skipPending}
          className="pv-button-secondary w-full disabled:opacity-60"
        >
          {skipPending ? t("onboardingWizard.skipping") : t("onboardingWizard.skipForNow")}
        </button>
      </aside>

      <div className="space-y-5">
        {needsWizard && step < 3 ? (
          <section className="pv-panel space-y-5 px-5 py-5 sm:px-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-zinc-700">
                  {t("onboardingWizard.stepCounter", { step: progress })}
                </p>
                <p className="text-sm text-zinc-500">3</p>
              </div>
              <div className="flex gap-2">
                {Array.from({ length: 3 }).map((_, index) => (
                  <span
                    key={`progress-${index + 1}`}
                    className={`h-2 flex-1 rounded-full ${
                      index < progress ? "bg-[var(--pv-brand)]" : "bg-zinc-200"
                    }`}
                  />
                ))}
              </div>
            </div>

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
          </section>
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
    </div>
  );
}
