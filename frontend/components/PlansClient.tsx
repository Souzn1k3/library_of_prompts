"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { ReactNode } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PlanPricingCard } from "@/components/plans/PlanPricingCard";
import { usePlansClientModel } from "@/components/plans/usePlansClientModel";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTierTranslationKey, languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import type { PlanRecord } from "@/lib/types";

type PlansClientProps = {
  plans: PlanRecord[];
  error: string | null;
};

const tierWorkloadLevel: Record<string, number> = {
  free: 1,
  starter: 2,
  pro: 3,
  enterprise: 4,
};

type ComparisonRow = {
  id: string;
  labelKey: TranslationKey;
  renderValue: (plan: PlanRecord) => ReactNode;
};

function computeMomentumScore(
  plan: PlanRecord,
  metrics: {
    maxUnlocks: number;
    maxDirectDiscount: number;
    maxTokenDiscount: number;
    maxFeatures: number;
  },
): number {
  const unlockPart = plan.monthly_paid_prompt_limit / metrics.maxUnlocks;
  const directPart = plan.prompt_purchase_discount_percent / metrics.maxDirectDiscount;
  const tokenPart = plan.lumen_purchase_discount_percent / metrics.maxTokenDiscount;
  const featurePart = plan.full_features.length / metrics.maxFeatures;

  return Math.round((unlockPart * 0.55 + directPart * 0.2 + tokenPart * 0.2 + featurePart * 0.05) * 100);
}

export function PlansClient({ plans, error }: PlansClientProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const searchParams = useSearchParams();
  const preferredTier = searchParams.get("tier");
  const billingState = searchParams.get("billing");
  const billingSessionId = searchParams.get("session_id");
  const billingTier = searchParams.get("tier");

  const {
    status,
    isAuthenticated,
    sortedPlans,
    currentTier,
    currentBillingStatusLabel,
    currentTierClass,
    currentStatusClass,
    actionError,
    pendingTier,
    expandedTier,
    portalError,
    portalPending,
    setExpandedTier,
    openBillingPortal,
    upgrade,
    isLowerOrEqualTier,
  } = usePlansClientModel({
    plans,
    preferredTier,
    billingState,
    billingSessionId,
    billingTier,
    t,
  });

  const metrics = {
    maxUnlocks: Math.max(...sortedPlans.map((plan) => plan.monthly_paid_prompt_limit), 1),
    maxDirectDiscount: Math.max(...sortedPlans.map((plan) => plan.prompt_purchase_discount_percent), 1),
    maxTokenDiscount: Math.max(...sortedPlans.map((plan) => plan.lumen_purchase_discount_percent), 1),
    maxFeatures: Math.max(...sortedPlans.map((plan) => plan.full_features.length), 1),
  };

  const comparisonRows: ComparisonRow[] = [
    {
      id: "included",
      labelKey: "plans.compareIncludedUnlocks",
      renderValue: (plan) => plan.monthly_paid_prompt_limit.toLocaleString(locale),
    },
    {
      id: "direct-discount",
      labelKey: "plans.compareDirectDiscount",
      renderValue: (plan) => `${plan.prompt_purchase_discount_percent}%`,
    },
    {
      id: "token-discount",
      labelKey: "plans.compareTokenDiscount",
      renderValue: (plan) => `${plan.lumen_purchase_discount_percent}%`,
    },
    {
      id: "features",
      labelKey: "plans.compareFeatureCoverage",
      renderValue: (plan) => plan.full_features.length.toLocaleString(locale),
    },
    {
      id: "workload",
      labelKey: "plans.compareWorkloadFit",
      renderValue: (plan) => t(`plans.compareWorkload.${plan.tier}` as TranslationKey),
    },
    {
      id: "momentum",
      labelKey: "plans.compareMomentumScore",
      renderValue: (plan) => {
        const score = computeMomentumScore(plan, metrics);
        return (
          <div className="space-y-1.5">
            <div className="h-2 overflow-hidden rounded-full bg-zinc-200">
              <div
                className="h-full rounded-full bg-zinc-900"
                style={{ width: `${score}%` }}
              />
            </div>
            <p className="text-xs font-semibold text-zinc-700">{score}/100</p>
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-5">
      {error ? (
        <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {actionError ?? portalError ? (
        <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {actionError ?? portalError}
        </div>
      ) : null}

      <section
        aria-label={t("plans.title")}
        className="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory [scrollbar-gutter:stable]"
      >
        {sortedPlans.map((plan) => (
          <div
            key={plan.tier}
            className="w-[min(22rem,calc(100vw-2.5rem))] shrink-0 snap-start lg:w-[min(24rem,calc(100vw-6rem))]"
          >
            <PlanPricingCard
              plan={plan}
              preferredTier={preferredTier}
              locale={locale}
              status={status}
              isAuthenticated={isAuthenticated}
              currentTier={currentTier}
              pendingTier={pendingTier}
              expanded={expandedTier === plan.tier}
              t={t}
              onToggleExpanded={() =>
                setExpandedTier((current) => (current === plan.tier ? null : plan.tier))
              }
              onUpgrade={(tier) => void upgrade(tier)}
              isLowerOrEqualTier={isLowerOrEqualTier}
            />
          </div>
        ))}
      </section>

      <section className="pv-panel px-5 py-5 sm:px-6">
        <div className="space-y-1.5">
          <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("plans.compareTitle")}</h2>
          <p className="text-sm text-zinc-600">{t("plans.compareSubtitle")}</p>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[46rem] border-separate border-spacing-0 text-left">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 rounded-l-[0.95rem] border border-[var(--pv-border)] bg-white px-3 py-3 text-xs uppercase tracking-[0.12em] text-zinc-500">
                  {t("plans.compareMetric")}
                </th>
                {sortedPlans.map((plan, index) => {
                  const isLast = index === sortedPlans.length - 1;
                  const isMaxPlan = plan.tier === "enterprise";

                  return (
                    <th
                      key={plan.tier}
                      className={`border border-[var(--pv-border)] px-3 py-3 text-center text-sm font-semibold text-zinc-900 ${
                        isLast ? "rounded-r-[0.95rem]" : ""
                      } ${isMaxPlan ? "pv-plans-compare-max-col" : "bg-white"}`}
                    >
                      {t(getTierTranslationKey(plan.tier))}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row, rowIndex) => {
                const isLastRow = rowIndex === comparisonRows.length - 1;

                return (
                  <tr key={row.id}>
                    <th
                      scope="row"
                      className={`sticky left-0 z-10 border border-[var(--pv-border)] bg-white px-3 py-3 text-sm font-medium text-zinc-700 ${
                        isLastRow ? "rounded-bl-[0.95rem]" : ""
                      }`}
                    >
                      {t(row.labelKey)}
                    </th>
                    {sortedPlans.map((plan, colIndex) => {
                      const isLastCol = colIndex === sortedPlans.length - 1;
                      const isMaxPlan = plan.tier === "enterprise";

                      return (
                        <td
                          key={`${row.id}-${plan.tier}`}
                          className={`border border-[var(--pv-border)] px-3 py-3 text-center text-sm text-zinc-900 ${
                            isLastRow && isLastCol ? "rounded-br-[0.95rem]" : ""
                          } ${isMaxPlan ? "pv-plans-compare-max-col" : "bg-white"}`}
                        >
                          {row.id === "workload" ? (
                            <div className="space-y-1">
                              <p className="font-medium">{row.renderValue(plan)}</p>
                              <div className="flex justify-center gap-1">
                                {Array.from({ length: 4 }).map((_, dotIndex) => (
                                  <span
                                    key={`${plan.tier}-dot-${dotIndex}`}
                                    className={`h-1.5 w-1.5 rounded-full ${
                                      dotIndex < (tierWorkloadLevel[plan.tier] ?? 1)
                                        ? "bg-zinc-900"
                                        : "bg-zinc-300"
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                          ) : (
                            row.renderValue(plan)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {status === "loading" ? (
        <p className="text-sm text-zinc-600">{t("dashboard.loading")}</p>
      ) : isAuthenticated ? (
        <section className="pv-panel px-5 py-5 text-sm text-zinc-700 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p>
              {t("plans.currentTier")}:{" "}
              <span className={`font-medium ${currentTierClass}`}>{t(getTierTranslationKey(currentTier))}</span>
              {currentBillingStatusLabel ? (
                <>
                  {" "}
                  · {t("plans.subscriptionStatus")}:{" "}
                  <span className={`font-medium ${currentStatusClass}`}>{currentBillingStatusLabel}</span>
                </>
              ) : null}
            </p>
            <button
              type="button"
              onClick={() => void openBillingPortal()}
              disabled={portalPending}
              className="pv-button-secondary disabled:opacity-60"
            >
              {portalPending ? t("plans.openingCheckout") : t("plans.manageBilling")}
            </button>
          </div>
        </section>
      ) : (
        <section className="pv-card-muted px-5 py-4 text-sm text-zinc-700">
          <p>
            <Link href={APP_ROUTES.signup} className="font-medium text-zinc-900 underline">
              {t("plans.createAccount")}
            </Link>{" "}
            {t("plans.createAccountSuffix")}
          </p>
        </section>
      )}

    </div>
  );
}
