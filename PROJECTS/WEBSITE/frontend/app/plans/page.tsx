import Link from "next/link";
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
    <div className="pv-page">
      <section className="pv-panel px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">
          <T k="plans.title" />
        </p>
        <h1 className="mt-3 pv-title text-zinc-950">
          <T k="plans.title" />
        </h1>
        <p className="mt-3 max-w-3xl text-base leading-relaxed text-[var(--pv-muted)]">
          <T k="plans.subtitle" />
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/catalog" className="pv-button-secondary">
            <T k="home.explorePrompts" />
          </Link>
          <Link href="/learn" className="pv-button-primary">
            <T k="home.startLearning" />
          </Link>
        </div>
      </section>
      <PlansClient plans={plans} error={error} />
    </div>
  );
}
