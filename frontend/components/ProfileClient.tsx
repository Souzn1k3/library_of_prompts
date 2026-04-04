"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import {
  BalanceCard,
  MoneyPipeline,
  MoneyStatusBlock,
  PayoutsTable,
  SellerTrustBlock,
  WhyZeroBalanceBlock,
} from "@/components/profile/MarketplacePanels";
import { PurchaseReviewCard } from "@/components/profile/PurchaseReviewCard";
import { useProfileData } from "@/components/profile/useProfileData";
import {
  formatDateTime,
  humanizeTrustIndicator,
  renderRating,
} from "@/components/profile/presentation";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { TOKEN_NAME_PLURAL } from "@/lib/constants/tokens";
import { formatDate, formatNumber } from "@/lib/formatters";
import { getTierTranslationKey, languageToIntlLocale } from "@/lib/i18n";
import type {
  SellerMarketplaceSummary,
} from "@/lib/types";

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

  const summary: SellerMarketplaceSummary = overview?.summary ?? {
    rating_average: user.rating_average ?? null,
    rating_display: user.rating_display ?? null,
    review_count: user.review_count ?? 0,
    sold_prompts_count: user.sold_prompts_count ?? 0,
    purchases_count: user.purchases_count ?? 0,
    seller_revenue_rub: user.seller_revenue_rub ?? 0,
    seller_lumens_earned: user.seller_lumens_earned ?? 0,
    pending_balance_rub: 0,
    available_balance_rub: 0,
    paid_out_rub: 0,
    refunded_balance_rub: 0,
    disputed_balance_rub: 0,
    pending_balance_lumens: 0,
    available_balance_lumens: 0,
    paid_out_lumens: 0,
    refunded_balance_lumens: 0,
    disputed_balance_lumens: 0,
    platform_commission_rub: 0,
    platform_commission_lumens: 0,
    clawback_due_rub: 0,
    clawback_due_lumens: 0,
    payout_eligible: false,
    trust_indicators: user.trust_indicators ?? [],
    recent_reviews: [],
    recent_payouts: [],
  };
  const payouts = overview?.payouts?.length ? overview.payouts : summary.recent_payouts;
  const purchases = overview?.purchases ?? [];
  const reviews = overview?.reviews ?? [];
  const ratingLabel = summary.rating_display ? `${summary.rating_display.toFixed(1)}/5` : t("profile.ratingNew");
  const reviewsAnchorHref = "#seller-reviews";
  const publicReviewsHref = user.contributor_slug
    ? appRoute.contributorBySlugReviewSort(user.contributor_slug, "best")
    : null;
  const planUnlocks =
    billing && billing.paid_prompt_limit_total > 0
      ? `${billing.paid_prompt_limit_remaining}/${billing.paid_prompt_limit_total}`
      : "0/0";

  return (
    <div className="space-y-6">
      <ProfileIntro authenticated={isAuthenticated} />

      <section className="pv-panel px-6 py-5 sm:px-7">
        <p className="pv-kicker">{t("profile.navTreeTitle")}</p>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-zinc-700">
          <Link href={APP_ROUTES.dashboard} className="pv-chip">{t("nav.dashboard")}</Link>
          <span aria-hidden="true">→</span>
          <Link href={APP_ROUTES.profile} className="pv-chip-brand">{t("profile.title")}</Link>
          <span aria-hidden="true">→</span>
          <span className="pv-chip">{t("profile.marketplaceKicker")}</span>
        </div>
        <p className="mt-3 text-sm text-zinc-600">{t("profile.navTreeBody")}</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="pv-card-muted p-4">
            <p className="pv-kicker">{t("profile.publicScopeTitle")}</p>
            <p className="mt-2 text-sm text-zinc-700">{t("profile.publicScopeBody")}</p>
          </div>
          <div className="pv-card-muted p-4">
            <p className="pv-kicker">{t("profile.privateScopeTitle")}</p>
            <p className="mt-2 text-sm text-zinc-700">{t("profile.privateScopeBody")}</p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <section className="pv-panel px-6 py-6 sm:px-7">
          <p className="pv-kicker">{t("profile.accountTitle")}</p>
          <h2 className="mt-3 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{user.display_name}</h2>
          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            <MetricCard label={t("profile.emailLabel")}>
              <p className="mt-3 font-medium text-zinc-900">{user.email}</p>
            </MetricCard>
            <MetricCard label={t("profile.memberSince")}>
              <p className="mt-3 font-medium text-zinc-900">{formatDate(user.created_at, locale)}</p>
            </MetricCard>
            <MetricCard label={t("profile.creatorRating")}>
              <p className="mt-3 font-medium text-zinc-900">{renderRating(summary.rating_display, t("profile.noReviewsYet"))}</p>
              <p className="mt-2 text-sm text-zinc-600">
                {ratingLabel} · {t("profile.reviewCountLabel", { count: summary.review_count })}
              </p>
              {user.contributor_slug ? (
                <Link
                  href={appRoute.contributorBySlugReviewSort(user.contributor_slug, "best")}
                  className="mt-2 inline-flex text-xs font-semibold text-[var(--pv-brand-strong)]"
                >
                  {t("profile.openPublicReviewPage")}
                </Link>
              ) : null}
            </MetricCard>
            <MetricCard label={t("profile.marketplaceSummary")}>
              <p className="mt-3 font-medium text-zinc-900">{t("profile.soldPromptsLabel", { count: summary.sold_prompts_count })}</p>
              <p className="mt-2 text-sm text-zinc-600">{t("profile.buyerPurchasesLabel", { count: summary.purchases_count })}</p>
            </MetricCard>
          </dl>

          {summary.trust_indicators.length ? (
            <div className="mt-5 flex flex-wrap gap-2">
              {summary.trust_indicators.map((indicator) => (
                <span key={indicator.key} className={indicator.level === "strong" ? "pv-badge-warning" : "pv-chip"}>
                  {humanizeTrustIndicator(indicator.key, t)}
                </span>
              ))}
            </div>
          ) : null}

          {user.contributor_slug ? (
            <Link
              href={appRoute.contributorBySlug(user.contributor_slug)}
              className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]"
            >
              {t("profile.publicCreatorProfile")}
              <span aria-hidden="true">↗</span>
            </Link>
          ) : null}
        </section>

        <div className="space-y-6">
          <section className="pv-panel px-6 py-6">
            <p className="pv-kicker">{t("profile.membershipTitle")}</p>
            <p className="mt-2 text-sm text-zinc-600">{t("profile.membershipPrivateNote")}</p>
            <div className="mt-4 grid gap-3 text-sm text-zinc-600">
              <div className="rounded-[1.25rem] border border-zinc-200 bg-white/75 p-4">
                <p>
                  {t("profile.planLabel")}:{" "}
                  <span className="font-medium text-zinc-900">{t(getTierTranslationKey(user.plan_tier))}</span>
                </p>
                <p className="mt-2">
                  {t("profile.includedPaidPrompts")}: <span className="font-medium text-zinc-900">{planUnlocks}</span>
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
                  <span className="font-medium text-zinc-900">{formatNumber(user.mission_credits ?? 0, locale)}</span>
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

            <Link href={APP_ROUTES.pricing} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand)]">
              {t("footer.pricing")}
              <span aria-hidden="true">↗</span>
            </Link>
          </section>

          <section className="pv-panel px-6 py-6">
            <p className="pv-kicker">{t("profile.actionsTitle")}</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <QuickLink href={APP_ROUTES.dashboard} label={t("profile.openDashboard")} />
              <QuickLink href={APP_ROUTES.wallet} label={t("profile.openWallet")} />
              <QuickLink href={APP_ROUTES.store} label={t("profile.openStore")} />
              {onboardingProfile?.needs_onboarding ? (
                <QuickLink href={APP_ROUTES.onboarding} label={t("profile.finishOnboarding")} />
              ) : null}
            </div>
          </section>
        </div>
      </div>

      {error ? (
        <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="pv-kicker">{t("profile.marketplaceKicker")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("profile.marketplaceTitle")}</h2>
            <p className="mt-2 text-sm text-zinc-600">{t("profile.marketplaceDescription")}</p>
          </div>
          <div className="rounded-[1rem] border border-zinc-200 bg-white/80 px-4 py-3 text-sm text-zinc-700">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">{t("profile.statusHintBadge")}</p>
            <p className="mt-1 font-medium text-zinc-950">
              {summary.payout_eligible ? t("profile.payoutEligible") : t("profile.settlementInProgress")}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {summary.payout_eligible
                ? t("profile.payoutEligibleDescription")
                : t("profile.settlementInProgressDescription")}
            </p>
            <p className="mt-2 text-[11px] text-zinc-500">{t("profile.statusHintNote")}</p>
          </div>
        </div>
        <div className="mt-4 rounded-[1rem] border border-zinc-200 bg-white/80 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                {t("profile.marketplaceSyncTitle")}
              </p>
              <p className="mt-1 text-sm text-zinc-700">{t("profile.marketplaceSyncDescription")}</p>
              <p className="mt-2 text-xs text-zinc-500">
                {lastMarketplaceSyncAt
                  ? t("profile.marketplaceSyncUpdatedAt", { date: formatDateTime(lastMarketplaceSyncAt, locale) })
                  : t("profile.marketplaceSyncNever")}
              </p>
            </div>
            <button
              type="button"
              onClick={reload}
              className="pv-button-secondary !w-auto"
            >
              {t("profile.marketplaceSyncAction")}
            </button>
          </div>
        </div>

        <div className="mt-6 space-y-5">
          <BalanceCard summary={summary} payouts={payouts} locale={locale} />
          <MoneyStatusBlock summary={summary} payouts={payouts} purchases={purchases} locale={locale} />
          <WhyZeroBalanceBlock summary={summary} purchases={purchases} locale={locale} />
          <MoneyPipeline summary={summary} payouts={payouts} purchases={purchases} locale={locale} />
          <PayoutsTable payouts={payouts} locale={locale} />
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="pv-kicker">{t("profile.purchasesLibraryKicker")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("profile.recentPurchasesTitle")}</h2>
            <p className="mt-2 text-sm text-zinc-600">{t("profile.recentPurchasesDescription")}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="pv-chip">{t("profile.totalPurchasesCount", { count: summary.purchases_count })}</span>
            <Link href={APP_ROUTES.catalog} className="pv-button-secondary !w-auto">
              {t("footer.browsePrompts")}
            </Link>
          </div>
        </div>

        {purchases.length ? (
          <div className="mt-6 space-y-4">
            {purchases.map((purchase) => (
              <PurchaseReviewCard
                key={purchase.id}
                locale={locale}
                purchase={purchase}
                onSubmitted={reload}
              />
            ))}
          </div>
        ) : (
          <p className="mt-6 text-sm text-zinc-500">
            {t("profile.noPurchases")}
          </p>
        )}
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <SellerTrustBlock
          summary={summary}
          ratingLabel={ratingLabel}
          reviewsHref={reviewsAnchorHref}
          publicReviewsHref={publicReviewsHref}
        />
      </section>

      <section id="seller-reviews" className="pv-panel px-6 py-6 sm:px-7">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="pv-kicker">{t("profile.recentReviews")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("profile.recentReviewsTitle")}</h2>
            <p className="mt-2 text-sm text-zinc-600">{t("profile.recentReviewsDescription")}</p>
          </div>
          {publicReviewsHref ? (
            <Link href={publicReviewsHref} className="text-sm font-semibold text-[var(--pv-brand)]">
              {t("profile.openPublicReviewPage")}
            </Link>
          ) : null}
        </div>

        {reviews.length ? (
          <div className="mt-6 space-y-3">
            {reviews.map((review) => (
              <div key={review.id} className="rounded-[1rem] border border-zinc-200 bg-white/75 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-zinc-900">{review.author_display_name}</p>
                    <p className="mt-1 text-xs text-zinc-500">{review.prompt_title}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-zinc-900">{renderRating(review.rating, t("profile.noReviewsYet"))}</p>
                    <p className="mt-1 text-xs text-zinc-500">{formatDate(review.created_at, locale)}</p>
                  </div>
                </div>
                {review.text ? <p className="mt-3 text-sm text-zinc-700">{review.text}</p> : null}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-6 text-sm text-zinc-500">{t("profile.noBuyerReviews")}</p>
        )}
      </section>
    </div>
  );
}

function ProfileIntro({ authenticated }: { authenticated: boolean }) {
  const { t } = useI18n();

  return (
    <PageIntro
      breadcrumbs={[
        { label: t("nav.dashboard"), href: authenticated ? APP_ROUTES.dashboard : undefined },
        { label: t("footer.account") },
        { label: t("profile.title") },
      ]}
      eyebrow={t("profile.title")}
      title={t("profile.title")}
      description={t("profile.subtitle")}
      actions={
        authenticated ? (
          <>
            <Link href={APP_ROUTES.dashboard} className="pv-button-primary">
              {t("nav.dashboard")}
            </Link>
            <Link href={APP_ROUTES.pricing} className="pv-button-secondary">
              {t("nav.billing")}
            </Link>
            <Link href={APP_ROUTES.wallet} className="pv-button-secondary">
              {t("nav.wallet")}
            </Link>
          </>
        ) : (
          <>
            <Link href={APP_ROUTES.login} className="pv-button-primary">
              {t("nav.login")}
            </Link>
            <Link href={APP_ROUTES.signup} className="pv-button-secondary">
              {t("nav.signup")}
            </Link>
          </>
        )
      }
    />
  );
}

function MetricCard({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/75 p-4">
      <dt className="pv-kicker">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function QuickLink({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="pv-button-secondary">
      {label}
    </Link>
  );
}
