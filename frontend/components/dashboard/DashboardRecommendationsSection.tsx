"use client";

import Link from "next/link";

import { PromptCard } from "@/components/PromptCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardRecommendationsSectionProps = {
  suggestions: PromptListItem[];
  needsOnboarding: boolean;
  t: Translate;
};

export function DashboardRecommendationsSection({
  suggestions,
  needsOnboarding,
  t,
}: DashboardRecommendationsSectionProps) {
  if (suggestions.length === 0 && !needsOnboarding) {
    return null;
  }

  return (
    <section id="recommendations" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("dashboard.recommendedForYou")}
          </h2>
        </div>
        <span className="pv-workspace-status">{suggestions.length + (needsOnboarding ? 1 : 0)}</span>
      </div>

      <div className="mt-6 space-y-4">
        {needsOnboarding ? (
          <div className="pv-alert pv-alert-warning">
            <p className="font-medium">{t("dashboard.finishOnboardingTitle")}</p>
            <p className="mt-2">
              <Link href={APP_ROUTES.onboarding} className="underline">
                {t("dashboard.finishOnboardingLink")}
              </Link>
            </p>
          </div>
        ) : null}

        {suggestions.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {suggestions.map((prompt) => (
              <PromptCard key={`dashboard-rec-${prompt.id}`} prompt={prompt} />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
