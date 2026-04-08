"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";

type OnboardingWizardHeaderProps = {
  needsWizard: boolean;
  progress: number;
  skipPending: boolean;
  onSkip: () => Promise<void>;
};

export function OnboardingWizardHeader({
  needsWizard,
  progress,
  skipPending,
  onSkip,
}: OnboardingWizardHeaderProps) {
  const { t } = useI18n();

  return (
    <div className="pv-panel flex flex-wrap items-center justify-between gap-3 px-5 py-4">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
          {t("onboardingWizard.activationSetup")}{" "}
          {needsWizard ? t("onboardingWizard.stepCounter", { step: progress }) : ""}
        </p>
        {needsWizard ? (
          <div className="flex gap-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <span
                key={`step-${index + 1}`}
                className={`h-2 rounded-full transition-all ${
                  index < progress ? "w-10 bg-[var(--pv-brand)]" : "w-6 bg-slate-200"
                }`}
              />
            ))}
          </div>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => void onSkip()}
        disabled={skipPending}
        className="pv-button-secondary !w-auto disabled:opacity-60"
      >
        {skipPending ? t("onboardingWizard.skipping") : t("onboardingWizard.skipForNow")}
      </button>
    </div>
  );
}
