import Link from "next/link";

import { OnboardingWizard } from "@/components/OnboardingWizard";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";

export default function OnboardingPage() {
  return (
    <div className="pv-page mx-auto max-w-5xl">
      <PageIntro
        breadcrumbs={[
          { label: <T k="nav.dashboard" />, href: "/dashboard" },
          { label: <T k="nav.onboarding" /> },
        ]}
        eyebrow={<T k="nav.onboarding" />}
        title={<T k="onboarding.pageTitle" />}
        description={<T k="onboarding.pageSubtitle" />}
        hint={<T k="dashboard.finishOnboardingTitle" />}
        actions={
          <>
            <Link href="/dashboard" className="pv-button-secondary">
              <T k="nav.dashboard" />
            </Link>
            <Link href="/catalog" className="pv-button-secondary">
              <T k="home.explorePrompts" />
            </Link>
          </>
        }
      />
      <OnboardingWizard />
    </div>
  );
}
