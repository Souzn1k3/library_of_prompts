"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { PlanPricingCard } from "@/components/plans/PlanPricingCard";
import { usePlansClientModel } from "@/components/plans/usePlansClientModel";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTierTranslationKey, languageToIntlLocale } from "@/lib/i18n";
import type { PlanRecord } from "@/lib/types";

type PlansClientProps = {
  plans: PlanRecord[];
  error: string | null;
};

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

  return (
    <div className="space-y-5">
      {error ? (
        <div className="pv-alert pv-alert-warning text-sm">
          {error}
        </div>
      ) : null}

      {actionError ?? portalError ? (
        <div className="pv-alert pv-alert-error text-sm">
          {actionError ?? portalError}
        </div>
      ) : null}

      <section
        aria-label={t("plans.title")}
        className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
      >
        {sortedPlans.map((plan) => (
          <div key={plan.tier} className="h-full">
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

      <section className="pv-card-muted px-4 py-4 sm:px-5">
        <div className="flex flex-wrap gap-2">
          <Link
            href={isAuthenticated ? APP_ROUTES.dashboard : APP_ROUTES.signup}
            className="pv-button-secondary"
          >
            {isAuthenticated ? t("nav.dashboard") : t("nav.signup")}
          </Link>
          <Link href={APP_ROUTES.catalog} className="pv-button-secondary">
            {t("home.explorePrompts")}
          </Link>
        </div>
        <Link href={APP_ROUTES.learnStart} className="mt-3 pv-button-secondary sm:w-auto">
          {t("home.startLearning")}
        </Link>
      </section>
    </div>
  );
}
