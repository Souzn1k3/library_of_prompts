"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { OnboardingWizardView } from "@/components/onboarding/OnboardingWizardView";
import { useOnboardingWizard } from "@/components/onboarding/useOnboardingWizard";

export function OnboardingWizard() {
  const { status } = useAuth();
  const wizard = useOnboardingWizard(status);

  return <OnboardingWizardView status={status} {...wizard} />;
}
