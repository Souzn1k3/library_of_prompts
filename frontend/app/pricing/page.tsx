import type { Metadata } from "next";

import { PlansClient } from "@/components/PlansClient";
import { T } from "@/components/i18n/T";
import { AppBreadcrumbs } from "@/components/navigation/AppBreadcrumbs";
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
    <div className="pv-page-sm">
      <section className="pv-panel px-5 py-5 sm:px-7 sm:py-6">
        <AppBreadcrumbs items={breadcrumbs} />
        <div className="mt-3 space-y-2">
          <h1 className="text-4xl font-bold tracking-[-0.04em] text-zinc-950 sm:text-5xl">
            <T k="plans.title" />
          </h1>
          <p className="max-w-3xl text-base leading-7 text-zinc-600">
            <T k="plans.subtitle" />
          </p>
        </div>
      </section>
      <PlansClient plans={plans} error={error} />
    </div>
  );
}
