"use client";

import Link from "next/link";

import { APP_ROUTES } from "@/lib/constants/routes";
import { formatNumber } from "@/lib/formatters";
import { getTierTranslationKey, type TranslationKey } from "@/lib/i18n";
import type { PlanRecord } from "@/lib/types";

type TranslateFn = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type PlanPricingCardProps = {
  plan: PlanRecord;
  preferredTier: string | null;
  locale: string;
  status: string;
  isAuthenticated: boolean;
  currentTier: string;
  pendingTier: string | null;
  expanded: boolean;
  t: TranslateFn;
  onToggleExpanded: () => void;
  onUpgrade: (tier: string) => void;
  isLowerOrEqualTier: (tier: string) => boolean;
};

export function PlanPricingCard({
  plan,
  preferredTier,
  locale,
  status,
  isAuthenticated,
  currentTier,
  pendingTier,
  expanded,
  t,
  onToggleExpanded,
  onUpgrade,
  isLowerOrEqualTier,
}: PlanPricingCardProps) {
  const isCurrent = plan.tier === currentTier;
  const isLowerOrEqual = isLowerOrEqualTier(plan.tier);
  const localizedTierName = t(getTierTranslationKey(plan.tier));
  const planDisplayName = localizedTierName || plan.name;
  const isMaxPlan = plan.tier === "enterprise";

  return (
    <div
      className={`pv-card p-5 ${
        preferredTier === plan.tier
          ? "border-zinc-900 ring-1 ring-zinc-900/20"
          : ""
      }`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <h2 className={`text-lg font-semibold ${isMaxPlan ? "text-[var(--pv-brand-strong)]" : "text-zinc-900"}`}>
          {planDisplayName}
        </h2>
        <div className="text-right text-sm text-zinc-600">
          <p className="font-semibold text-zinc-900">
            {plan.price_rub_month > 0 ? `${formatNumber(plan.price_rub_month, locale)} RUB` : t("plans.priceFree")}
          </p>
          {plan.price_usd_month > 0 ? (
            <p className="text-zinc-500">${formatNumber(plan.price_usd_month, locale)}{t("plans.perMonth")}</p>
          ) : (
            <p className="text-zinc-500">{t("plans.perMonth")}</p>
          )}
        </div>
      </div>
      {plan.description ? <p className="mt-1 text-sm text-zinc-600">{plan.description}</p> : null}
      <div className="mt-4 grid gap-2 text-sm text-zinc-700">
        <div className="rounded-[0.75rem] border border-zinc-200 bg-white/70 p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">{t("plans.includedPaidPrompts")}</p>
          <p className="mt-2 text-2xl font-semibold text-zinc-950">{formatNumber(plan.monthly_paid_prompt_limit, locale)}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("plans.includedPaidPromptsBody")}</p>
        </div>
        {plan.highlights.map((item) => (
          <div key={item} className="rounded-[0.625rem] border border-zinc-200 bg-zinc-50/80 px-3 py-2">
            {item}
          </div>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-xs text-zinc-500">
        <span className="pv-chip">{t("plans.directBuyDiscount", { value: plan.prompt_purchase_discount_percent })}</span>
        <span className="pv-chip">{t("plans.lumenDiscount", { value: plan.lumen_purchase_discount_percent })}</span>
      </div>
      <button
        type="button"
        onClick={onToggleExpanded}
        className="mt-4 text-sm font-semibold text-[var(--pv-brand-strong)]"
      >
        {expanded ? t("plans.hideFeatures") : t("plans.showFeatures")}
      </button>
      {expanded ? (
        <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-zinc-700">
          {plan.full_features.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      ) : null}
      <div className="mt-4">
        {status === "loading" ? (
          <span className="inline-flex items-center rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
            {t("dashboard.loading")}
          </span>
        ) : !isAuthenticated ? (
          <Link href={APP_ROUTES.signup} className="pv-button-secondary">
            {t("plans.createAccountCta")}
          </Link>
        ) : isCurrent ? (
          <span className="inline-flex items-center rounded-full border border-[rgba(29,78,216,0.24)] bg-[rgba(29,78,216,0.1)] px-3 py-2 text-sm font-medium text-[var(--pv-brand-strong)]">
            {t("plans.currentPlan")}
          </span>
        ) : isLowerOrEqual ? (
          <span className="inline-flex items-center rounded-full bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-700">
            {t("plans.included")}
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onUpgrade(plan.tier)}
            disabled={pendingTier === plan.tier}
            className="pv-button-primary disabled:opacity-60"
          >
            {pendingTier === plan.tier
              ? t("plans.openingCheckout")
              : t("plans.upgradeTo", { plan: planDisplayName })}
          </button>
        )}
      </div>
    </div>
  );
}
