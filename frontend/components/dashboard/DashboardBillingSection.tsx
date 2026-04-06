import Link from "next/link";

import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardBillingSectionProps = {
  t: Translate;
  planLabel: string;
  highlightedPlanClassName: string;
  highlightedStatusClassName: string;
  localizedBillingStatus: string | null;
  portalPending: boolean;
  portalError: string | null;
  onOpenPortal: () => void;
};

export function DashboardBillingSection({
  t,
  planLabel,
  highlightedPlanClassName,
  highlightedStatusClassName,
  localizedBillingStatus,
  portalPending,
  portalError,
  onOpenPortal,
}: DashboardBillingSectionProps) {
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("nav.billing")}</h2>
          <p className="mt-2 text-sm text-zinc-600">{t("dashboard.billingBody")}</p>
        </div>
        <span className={`pv-workspace-status ${highlightedPlanClassName}`}>{planLabel}</span>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <div className="pv-card p-4">
          <p className="pv-kicker">{t("plans.currentTier")}</p>
          <p className={`mt-2 text-base font-semibold ${highlightedPlanClassName}`}>{planLabel}</p>
        </div>
        <div className="pv-card p-4">
          <p className="pv-kicker">{t("plans.subscriptionStatus")}</p>
          <p className={`mt-2 text-base font-semibold ${highlightedStatusClassName}`}>
            {localizedBillingStatus ?? t("plans.billingStatus.unknown")}
          </p>
        </div>
        <div className="pv-card p-4">
          <p className="pv-kicker">{t("dashboard.manageBilling")}</p>
          <p className="mt-2 pv-hint-badge">{t("common.hintBadge")}</p>
          <p className="mt-1 text-sm text-zinc-700">{t("dashboard.billingActionHint")}</p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onOpenPortal}
          disabled={portalPending}
          className="pv-button-secondary disabled:opacity-60"
        >
          {portalPending ? t("plans.openingCheckout") : t("dashboard.manageBilling")}
        </button>
        <Link href={APP_ROUTES.pricing} className="pv-button-primary">
          {t("dashboard.changePlan")}
        </Link>
      </div>
      {portalError ? <p className="mt-3 text-sm text-red-700">{portalError}</p> : null}
    </section>
  );
}
