import Link from "next/link";

import { OnboardingWizard } from "@/components/OnboardingWizard";
import { T } from "@/components/i18n/T";

export default function OnboardingPage() {
  return (
    <div className="pv-page mx-auto max-w-5xl">
      <section className="pv-panel px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">
          <T k="onboarding.pageTitle" />
        </p>
        <h1 className="mt-3 pv-title text-zinc-950">
          <T k="onboarding.pageTitle" />
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
          <T k="onboarding.pageSubtitle" />
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/dashboard" className="pv-button-secondary">
            <T k="nav.dashboard" />
          </Link>
          <Link href="/catalog" className="pv-button-primary">
            <T k="home.explorePrompts" />
          </Link>
        </div>
      </section>
      <OnboardingWizard />
    </div>
  );
}
