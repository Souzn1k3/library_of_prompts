import Link from "next/link";

import { OnboardingWizard } from "@/components/OnboardingWizard";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { getServerAuthCookieState } from "@/lib/server-auth";

export default async function OnboardingPage() {
  const authState = await getServerAuthCookieState();

  return (
    <div className="pv-page mx-auto max-w-5xl">
      <PageIntro
        breadcrumbs={authState.hasAnyAuthCookie
          ? [
            { label: <T k="nav.dashboard" />, href: "/dashboard" },
            { label: <T k="nav.onboarding" /> },
          ]
          : [
            { label: <T k="brand.name" />, href: "/" },
            { label: <T k="nav.onboarding" /> },
          ]}
        eyebrow={<T k="nav.onboarding" />}
        title={<T k="onboarding.pageTitle" />}
        description={<T k="onboarding.pageSubtitle" />}
        hint={<T k="dashboard.finishOnboardingTitle" />}
        actions={
          <>
            {authState.hasAnyAuthCookie ? (
              <Link href="/dashboard" className="pv-button-secondary">
                <T k="nav.dashboard" />
              </Link>
            ) : (
              <Link href="/login" className="pv-button-secondary">
                <T k="nav.login" />
              </Link>
            )}
            <Link href="/catalog" className="pv-inline-link">
              <T k="home.explorePrompts" />
              <span aria-hidden="true">↗</span>
            </Link>
          </>
        }
      />
      <OnboardingWizard />
    </div>
  );
}
