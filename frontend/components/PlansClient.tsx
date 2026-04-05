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
    <div className="space-y-6">
      {error ? (
        <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {status === "loading" ? (
        <p className="text-sm text-zinc-600">{t("dashboard.loading")}</p>
      ) : isAuthenticated ? (
        <div className="pv-panel px-5 py-5 text-sm text-zinc-700 sm:px-6">
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
          <div className="mt-3">
            <button
              type="button"
              onClick={() => void openBillingPortal()}
              disabled={portalPending}
              className="pv-button-secondary disabled:opacity-60"
            >
              {portalPending ? t("plans.openingCheckout") : t("plans.manageBilling")}
            </button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-zinc-600">
          <Link href={APP_ROUTES.signup} className="font-medium text-zinc-900 underline">
            {t("plans.createAccount")}
          </Link>{" "}
          {t("plans.createAccountSuffix")}
        </p>
      )}

      {actionError ?? portalError ? (
        <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {actionError ?? portalError}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {sortedPlans.map((plan) => (
          <PlanPricingCard
            key={plan.tier}
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
        ))}
      </div>
    </div>
  );
}
