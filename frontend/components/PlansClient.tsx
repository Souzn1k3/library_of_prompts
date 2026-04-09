"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { usePlansClientModel } from "@/components/plans/usePlansClientModel";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTierTranslationKey, languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import type { PlanRecord } from "@/lib/types";

type PlansClientProps = {
  plans: PlanRecord[];
  error: string | null;
};

type ComparisonItem = {
  labelKey: TranslationKey;
  value: string;
};

function formatPlanPrice(plan: PlanRecord, locale: string) {
  const amount = plan.price_rub_month > 0 ? plan.price_rub_month : plan.price_usd_month;
  const currency = plan.price_rub_month > 0 ? "RUB" : "USD";

  if (amount === 0) {
    return null;
  }

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

function bestFitKeyForTier(tier: string): TranslationKey {
  switch (tier) {
    case "free":
      return "plans.compareWorkload.free";
    case "starter":
      return "plans.compareWorkload.starter";
    case "pro":
      return "plans.compareWorkload.pro";
    default:
      return "plans.compareWorkload.enterprise";
  }
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

  return (
    <div className="space-y-6">
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

      <section className="grid gap-4 xl:grid-cols-4">
        {sortedPlans.map((plan) => {
          const isCurrent = currentTier === plan.tier;
          const isPreferred = preferredTier === plan.tier;
          const priceLabel = formatPlanPrice(plan, locale);
          const isExpanded = expandedTier === plan.tier;
          const comparison: ComparisonItem[] = [
            {
              labelKey: "plans.compareIncludedUnlocks",
              value: plan.monthly_paid_prompt_limit.toLocaleString(locale),
            },
            {
              labelKey: "plans.compareDirectDiscount",
              value: `${plan.prompt_purchase_discount_percent}%`,
            },
            {
              labelKey: "plans.compareTokenDiscount",
              value: `${plan.lumen_purchase_discount_percent}%`,
            },
            {
              labelKey: "plans.compareWorkloadFit",
              value: t(bestFitKeyForTier(plan.tier)),
            },
          ];
          const featureList = isExpanded ? plan.full_features : plan.highlights.slice(0, 4);

          return (
            <article
              key={plan.tier}
              className={`pv-card flex h-full flex-col p-6 ${
                isCurrent
                  ? "border-[var(--pv-brand)]/30 shadow-[0_20px_42px_rgba(15,91,255,0.12)]"
                  : isPreferred
                    ? "border-[var(--pv-border-strong)]"
                    : ""
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
                  <p className="pv-kicker">{t(getTierTranslationKey(plan.tier))}</p>
                  <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-950">
                    {plan.name}
                  </h2>
                  <p className="text-sm leading-relaxed text-zinc-600">
                    {plan.description || t(bestFitKeyForTier(plan.tier))}
                  </p>
                </div>
                {isCurrent ? (
                  <span className="pv-chip-brand">{t("plans.currentTier")}</span>
                ) : isPreferred ? (
                  <span className="pv-chip-brand">{t(getTierTranslationKey(plan.tier))}</span>
                ) : null}
              </div>

              <div className="mt-6 rounded-[1.4rem] border border-[var(--pv-border)] bg-white/78 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
                  {priceLabel ? t("plans.title") : t("plans.currentTier")}
                </p>
                <p className="mt-2 text-3xl font-semibold tracking-[-0.06em] text-zinc-950">
                  {priceLabel ?? t("plans.priceFree")}
                </p>
                <p className="mt-2 text-sm text-zinc-600">
                  {plan.highlights[0] ?? t(bestFitKeyForTier(plan.tier))}
                </p>
              </div>

              <div className="mt-5 grid gap-2">
                {comparison.map((item) => (
                  <div
                    key={`${plan.tier}-${item.labelKey}`}
                    className="flex items-center justify-between gap-3 rounded-[1rem] border border-[var(--pv-border)] bg-white/68 px-4 py-3"
                  >
                    <span className="text-xs font-medium uppercase tracking-[0.12em] text-zinc-500">
                      {t(item.labelKey)}
                    </span>
                    <span className="text-sm font-semibold text-zinc-950">{item.value}</span>
                  </div>
                ))}
              </div>

              <div className="mt-5 space-y-2">
                {featureList.map((feature) => (
                  <div key={`${plan.tier}-${feature}`} className="rounded-[1rem] bg-[var(--pv-brand-soft)]/40 px-3 py-2.5 text-sm text-zinc-700">
                    {feature}
                  </div>
                ))}
              </div>

              {plan.full_features.length > plan.highlights.length ? (
                <button
                  type="button"
                  onClick={() => setExpandedTier((current) => (current === plan.tier ? null : plan.tier))}
                  className="mt-4 text-left text-sm font-semibold text-[var(--pv-brand-strong)]"
                >
                  {isExpanded ? t("plans.hideFeatures") : t("plans.showFeatures")}
                </button>
              ) : null}

              <div className="mt-auto pt-6">
                {!isAuthenticated ? (
                  <Link href={APP_ROUTES.signup} className="pv-button-primary w-full">
                    {t("plans.createAccount")}
                  </Link>
                ) : isCurrent ? (
                  <button
                    type="button"
                    onClick={() => void openBillingPortal()}
                    disabled={portalPending}
                    className="pv-button-primary w-full disabled:opacity-60"
                  >
                    {portalPending ? t("plans.openingCheckout") : t("plans.manageBilling")}
                  </button>
                ) : isLowerOrEqualTier(plan.tier) ? (
                  <button
                    type="button"
                    disabled
                    className="pv-button-secondary w-full cursor-not-allowed opacity-70"
                  >
                    {t("plans.currentTier")}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => void upgrade(plan.tier)}
                    disabled={pendingTier === plan.tier}
                    className="pv-button-primary w-full disabled:opacity-60"
                  >
                    {pendingTier === plan.tier
                      ? t("plans.openingCheckout")
                      : t("plans.upgradeTo", { plan: t(getTierTranslationKey(plan.tier)) })}
                  </button>
                )}
              </div>
            </article>
          );
        })}
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.05em] text-zinc-950">{t("plans.compareTitle")}</h2>
            <p className="text-sm leading-relaxed text-zinc-600">{t("plans.compareSubtitle")}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          {sortedPlans.map((plan) => (
            <article key={`summary-${plan.tier}`} className="rounded-[1.5rem] border border-[var(--pv-border)] bg-white/72 p-5">
              <p className="pv-kicker">{t(getTierTranslationKey(plan.tier))}</p>
              <h3 className="mt-2 text-xl font-semibold tracking-[-0.04em] text-zinc-950">{plan.name}</h3>
              <div className="mt-4 space-y-3 text-sm text-zinc-700">
                <div className="flex items-center justify-between gap-3">
                  <span>{t("plans.compareIncludedUnlocks")}</span>
                  <span className="font-semibold text-zinc-950">{plan.monthly_paid_prompt_limit}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>{t("plans.compareDirectDiscount")}</span>
                  <span className="font-semibold text-zinc-950">{plan.prompt_purchase_discount_percent}%</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>{t("plans.compareTokenDiscount")}</span>
                  <span className="font-semibold text-zinc-950">{plan.lumen_purchase_discount_percent}%</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>{t("plans.compareFeatureCoverage")}</span>
                  <span className="font-semibold text-zinc-950">{plan.full_features.length}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {status === "loading" ? (
        <p className="text-sm text-zinc-600">{t("dashboard.loading")}</p>
      ) : isAuthenticated ? (
        <section className="pv-panel px-6 py-5 text-sm text-zinc-700 sm:px-7">
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
              className="pv-button-secondary !w-auto disabled:opacity-60"
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
