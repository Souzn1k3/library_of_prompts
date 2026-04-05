"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_NAME_PLURAL } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import { getTierTranslationKey } from "@/lib/i18n";
import type { BillingStatus, SellerMarketplaceSummary, UserProfile } from "@/lib/types";

type ProfileMembershipPanelProps = {
  user: UserProfile;
  summary: SellerMarketplaceSummary;
  billing: BillingStatus | null;
  planUnlocks: string;
  locale: string;
};

export function ProfileMembershipPanel({
  user,
  summary,
  billing,
  planUnlocks,
  locale,
}: ProfileMembershipPanelProps) {
  const { t } = useI18n();

  return (
    <section className="pv-panel px-6 py-6">
      <p className="pv-kicker">{t("profile.membershipTitle")}</p>
      <p className="mt-2 text-sm text-zinc-600">{t("profile.membershipPrivateNote")}</p>
      <div className="mt-4 grid gap-3 text-sm text-zinc-600">
        <div className="rounded-[1.25rem] border border-zinc-200 bg-white/75 p-4">
          <p>
            {t("profile.planLabel")}:{" "}
            <span className="font-medium text-zinc-900">
              {t(getTierTranslationKey(user.plan_tier))}
            </span>
          </p>
          <p className="mt-2">
            {t("profile.includedPaidPrompts")}:{" "}
            <span className="font-medium text-zinc-900">{planUnlocks}</span>
          </p>
          <p className="mt-2">
            {t("profile.directPurchaseDiscount")}:{" "}
            <span className="font-medium text-zinc-900">
              {billing?.prompt_purchase_discount_percent ?? 0}%
            </span>
          </p>
          <p className="mt-2">
            {t("profile.lumenPurchaseDiscount")}:{" "}
            <span className="font-medium text-zinc-900">
              {billing?.lumen_purchase_discount_percent ?? 0}%
            </span>
          </p>
        </div>

        <div className="rounded-[1.25rem] border border-zinc-200 bg-white/75 p-4">
          <p>
            {t("profile.creditsLabel")}:{" "}
            <span className="font-medium text-zinc-900">
              {formatNumber(user.mission_credits ?? 0, locale)}
            </span>
          </p>
          <p className="mt-2">
            {t("profile.revenueLedger")}:{" "}
            <span className="font-medium text-zinc-900">
              {formatNumber(summary.seller_revenue_rub, locale)} RUB
            </span>
          </p>
          <p className="mt-2">
            {t("profile.lumensEarned")}:{" "}
            <span className="font-medium text-zinc-900">
              {formatNumber(summary.seller_lumens_earned, locale)} {TOKEN_NAME_PLURAL}
            </span>
          </p>
        </div>
      </div>

      <Link
        href={APP_ROUTES.pricing}
        className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]"
      >
        {t("footer.pricing")}
        <span aria-hidden="true">↗</span>
      </Link>
    </section>
  );
}
