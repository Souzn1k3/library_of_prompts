"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { SellerTrustBlock } from "@/components/profile/MarketplacePanels";
import { ProfileIntro } from "@/components/profile/ProfileIntro";
import { ProfileMarketplaceSection } from "@/components/profile/ProfileMarketplaceSection";
import { ProfilePrimarySection } from "@/components/profile/ProfilePrimarySection";
import { ProfilePurchasesSection } from "@/components/profile/ProfilePurchasesSection";
import { ProfileReviewsSection } from "@/components/profile/ProfileReviewsSection";
import { useProfileData } from "@/components/profile/useProfileData";
import { useProfileViewModel } from "@/components/profile/useProfileViewModel";
import {
  APP_ROUTES,
} from "@/lib/constants/routes";
import { languageToIntlLocale } from "@/lib/i18n";

export function ProfileClient() {
  const { status, user } = useAuth();
  const { language, t } = useI18n();
  const isAuthenticated = status === "authenticated" && Boolean(user);
  const locale = useMemo(() => languageToIntlLocale(language), [language]);
  const marketplaceUnavailable = t("profile.marketplaceUnavailable");
  const {
    overview,
    billing,
    onboardingProfile,
    error,
    lastMarketplaceSyncAt,
    reload,
  } = useProfileData({
    status,
    isAuthenticated,
    marketplaceUnavailableMessage: marketplaceUnavailable,
  });
  const {
    summary,
    payouts,
    purchases,
    reviews,
    ratingLabel,
    publicReviewsHref,
    reviewsAnchorHref,
    planUnlocks,
  } = useProfileViewModel({
    user,
    overview,
    billing,
    t,
  });

  if (status === "loading") {
    return (
      <div className="space-y-6">
        <ProfileIntro authenticated={false} />
        <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>
      </div>
    );
  }

  if (status === "unauthenticated" || !user) {
    return (
      <div className="space-y-6">
        <ProfileIntro authenticated={false} />
        <p className="text-sm text-zinc-600">
          {t("profile.signInPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
            {t("profile.signInLink")}
          </Link>{" "}
          {t("profile.signInSuffix")}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ProfileIntro authenticated={isAuthenticated} />
      <ProfilePrimarySection
        user={user}
        summary={summary}
        billing={billing}
        onboardingProfile={onboardingProfile}
        ratingLabel={ratingLabel}
        planUnlocks={planUnlocks}
        locale={locale}
      />

      {error ? (
        <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      <ProfileMarketplaceSection
        summary={summary}
        payouts={payouts}
        purchases={purchases}
        locale={locale}
        lastMarketplaceSyncAt={lastMarketplaceSyncAt}
        onReload={reload}
      />
      <ProfilePurchasesSection
        summary={summary}
        purchases={purchases}
        locale={locale}
        onReload={reload}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <SellerTrustBlock
          summary={summary}
          ratingLabel={ratingLabel}
          reviewsHref={reviewsAnchorHref}
          publicReviewsHref={publicReviewsHref}
        />
      </section>

      <ProfileReviewsSection reviews={reviews} publicReviewsHref={publicReviewsHref} locale={locale} />
    </div>
  );
}
