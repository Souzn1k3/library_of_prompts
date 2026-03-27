import { OnboardingWizard } from "@/components/OnboardingWizard";
import { T } from "@/components/i18n/T";

export default function OnboardingPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="onboarding.pageTitle" />
        </h1>
        <p className="text-sm text-zinc-600">
          <T k="onboarding.pageSubtitle" />
        </p>
      </header>
      <OnboardingWizard />
    </div>
  );
}
