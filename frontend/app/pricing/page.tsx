import Link from "next/link";
import type { Metadata } from "next";

import { PlansClient } from "@/components/PlansClient";
import { T } from "@/components/i18n/T";
import { PageIntro } from "@/components/navigation/PageIntro";
import { ApiRequestError, fetchPlans } from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { getServerAuthCookieState } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return {
    title: getTranslation(language, "meta.plansTitle"),
    description: getTranslation(language, "meta.plansDescription"),
  };
}

export const revalidate = 300;

export default async function PricingPage() {
  const language = await getServerLanguage();
  const authState = await getServerAuthCookieState();
  const breadcrumbs = authState.hasAnyAuthCookie
    ? [
        { label: <T k="nav.dashboard" />, href: "/dashboard" },
        { label: <T k="footer.account" /> },
        { label: <T k="nav.billing" /> },
      ]
    : [
        { label: <T k="brand.name" />, href: "/" },
        { label: <T k="nav.plans" /> },
      ];
  let plans: Awaited<ReturnType<typeof fetchPlans>> = [];
  let error: string | null = null;
  try {
    plans = await fetchPlans(language);
  } catch (e) {
    error = e instanceof ApiRequestError ? e.message : getTranslation(language, "plans.loadFailed");
  }

  return (
    <div className="pv-page">
      <PageIntro
        breadcrumbs={breadcrumbs}
        eyebrow={<T k="nav.plans" />}
        title={<T k="plans.title" />}
        description={<T k="plans.subtitle" />}
        actions={(
          <>
            <Link href={authState.hasAnyAuthCookie ? "/dashboard" : "/signup"} className="pv-button-primary">
              <T k={authState.hasAnyAuthCookie ? "nav.dashboard" : "nav.signup"} />
            </Link>
            <Link href="/catalog" className="pv-button-secondary">
              <T k="home.explorePrompts" />
            </Link>
          </>
        )}
        aside={(
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="pv-stat-card">
              <p className="pv-stat-label">
                <T k="nav.plans" />
              </p>
              <p className="mt-3 text-2xl font-semibold text-zinc-950">{plans.length}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">
                <T k="plans.compareTitle" />
              </p>
              <p className="mt-3 text-sm text-zinc-600">
                <T k="plans.compareSubtitle" />
              </p>
            </div>
          </div>
        )}
      />
      <PlansClient plans={plans} error={error} />
    </div>
  );
}
