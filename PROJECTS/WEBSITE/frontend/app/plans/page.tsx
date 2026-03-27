import type { Metadata } from "next";

import { PlansClient } from "@/components/PlansClient";
import { T } from "@/components/i18n/T";
import { ApiRequestError, fetchPlans } from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { getServerLanguage } from "@/lib/server-i18n";

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return {
    title: getTranslation(language, "meta.plansTitle"),
    description: getTranslation(language, "meta.plansDescription"),
  };
}

export const revalidate = 300;

export default async function PlansPage() {
  const language = await getServerLanguage();
  let plans: Awaited<ReturnType<typeof fetchPlans>> = [];
  let error: string | null = null;
  try {
    plans = await fetchPlans(language);
  } catch (e) {
    error = e instanceof ApiRequestError ? e.message : getTranslation(language, "plans.loadFailed");
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="plans.title" />
        </h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          <T k="plans.subtitle" />
        </p>
      </header>
      <PlansClient plans={plans} error={error} />
    </div>
  );
}
