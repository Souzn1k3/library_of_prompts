"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { ApiRequestError } from "@/lib/api";
import { fetchBillingStatus, fetchMarketplaceOverview, fetchOnboardingProfile, upsertPromptReview } from "@/lib/client-api";
import { APP_ROUTES, appRoute } from "@/lib/constants/routes";
import { formatDate, formatNumber, humanizeSnakeCase } from "@/lib/formatters";
import { getTierTranslationKey, languageToIntlLocale } from "@/lib/i18n";
import type {
  BillingStatus,
  OnboardingProfile,
  MarketplacePayout,
  MarketplaceOverview,
  PromptMarketplacePurchase,
  PromptReview,
  ReviewModerationStatus,
  SellerMarketplaceSummary,
} from "@/lib/types";

type TranslateFn = (key: string, params?: Record<string, string | number | null | undefined>) => string;

const TRUST_INDICATOR_LABELS: Record<string, string> = {
  verified_creator: "profile.trustVerifiedCreator",
  top_contributor: "profile.trustTopContributor",
  high_rating: "profile.trustHighRating",
  top_seller: "profile.trustTopSeller",
  new_marketplace_profile: "profile.trustNewMarketplaceProfile",
};

const PAYMENT_METHOD_LABELS: Record<PromptMarketplacePurchase["payment_method"], string> = {
  included_limit: "profile.paymentMethodIncludedLimit",
  lumens: "profile.paymentMethodLumens",
  legacy_store: "profile.paymentMethodLegacyStore",
  stripe: "profile.paymentMethodDirectCheckout",
};

const PURCHASE_STATUS_LABELS: Record<PromptMarketplacePurchase["status"], string> = {
  pending: "profile.purchaseStatusPending",
  completed: "profile.purchaseStatusCompleted",
  failed: "profile.purchaseStatusFailed",
  canceled: "profile.purchaseStatusCanceled",
  refunded: "profile.purchaseStatusRefunded",
};

const SETTLEMENT_STATUS_LABELS: Record<Exclude<PromptMarketplacePurchase["settlement_status"], undefined>, string> = {
  pending: "profile.settlementStatusPending",
  available: "profile.settlementStatusAvailable",
  paid_out: "profile.settlementStatusPaidOut",
  refunded: "profile.settlementStatusRefunded",
  disputed: "profile.settlementStatusDisputed",
};

const PAYOUT_STATUS_LABELS: Record<MarketplacePayout["status"], string> = {
  requested: "profile.payoutStatusRequested",
  processing: "profile.payoutStatusProcessing",
  paid: "profile.payoutStatusPaid",
  failed: "profile.payoutStatusFailed",
  canceled: "profile.payoutStatusCanceled",
};

const REVIEW_MODERATION_STATUS_LABELS: Record<ReviewModerationStatus, string> = {
  visible: "profile.reviewModerationVisible",
  pending: "profile.reviewModerationPending",
  hidden: "profile.reviewModerationHidden",
};

const REVIEW_MODERATION_REASON_LABELS: Record<string, string> = {
  refunded_purchase: "profile.reviewReasonRefundedPurchase",
  reported_by_users: "profile.reviewReasonReportedByUsers",
  review_velocity: "profile.reviewReasonReviewVelocity",
  repeat_buyer_seller_pattern: "profile.reviewReasonRepeatBuyerSellerPattern",
  dense_buyer_seller_activity: "profile.reviewReasonDenseBuyerSellerActivity",
  duplicate_review_text: "profile.reviewReasonDuplicateReviewText",
};

export function ProfileClient() {
  const { status, user } = useAuth();
  const { language, t } = useI18n();
  const isAuthenticated = status === "authenticated" && Boolean(user);
  const [overview, setOverview] = useState<MarketplaceOverview | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [onboardingProfile, setOnboardingProfile] = useState<OnboardingProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [lastMarketplaceSyncAt, setLastMarketplaceSyncAt] = useState<string | null>(null);
  const locale = useMemo(() => languageToIntlLocale(language), [language]);
  const marketplaceUnavailable = t("profile.marketplaceUnavailable");

  useEffect(() => {
    if (status !== "authenticated" || !user) {
      setOverview(null);
      setBilling(null);
      setOnboardingProfile(null);
      setLastMarketplaceSyncAt(null);
      return;
    }

    let cancelled = false;

    Promise.allSettled([fetchMarketplaceOverview(), fetchBillingStatus(), fetchOnboardingProfile()])
      .then((results) => {
        if (cancelled) {
          return;
        }

        const [overviewResult, billingResult, onboardingResult] = results;

        if (overviewResult.status === "fulfilled") {
          setOverview(overviewResult.value);
        }
        if (billingResult.status === "fulfilled") {
          setBilling(billingResult.value);
        }
        if (onboardingResult.status === "fulfilled") {
          setOnboardingProfile(onboardingResult.value);
        }
        if (
          overviewResult.status === "fulfilled" ||
          billingResult.status === "fulfilled" ||
          onboardingResult.status === "fulfilled"
        ) {
          setLastMarketplaceSyncAt(new Date().toISOString());
        }

        const firstError = [overviewResult, billingResult].find((result) => result.status === "rejected");
        if (!firstError || firstError.status !== "rejected") {
          setError(null);
          return;
        }
        setError(
          firstError.reason instanceof ApiRequestError
            ? firstError.reason.message
            : marketplaceUnavailable,
        );
      })
      .catch(() => {
        if (!cancelled) {
          setError(marketplaceUnavailable);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [marketplaceUnavailable, reloadToken, status, user]);

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
                    {formatNumber(summary.seller_lumens_earned, locale)} LMN
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
              onClick={() => setReloadToken((value) => value + 1)}
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
                onSubmitted={() => setReloadToken((value) => value + 1)}
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

function StatusMetric({ title, value, caption }: { title: string; value: string; caption?: string }) {
  return (
    <div className="rounded-[1rem] border border-zinc-200/80 bg-white p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{title}</p>
      <p className="mt-2 text-sm font-semibold text-zinc-900">{value}</p>
      {caption ? <p className="mt-1 text-xs text-zinc-500">{caption}</p> : null}
    </div>
  );
}

function BalanceCard({
  summary,
  payouts,
  locale,
}: {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  locale: string;
}) {
  const { t } = useI18n();
  const nextPayout = findUpcomingPayout(payouts);
  const nextPayoutDate = nextPayout ? formatDate(nextPayout.requested_at, locale) : t("profile.noData");

  return (
    <div className="rounded-[1.75rem] border border-zinc-200 bg-white p-6 shadow-[0_1px_0_rgba(0,0,0,0.04)] sm:p-7">
      <p className="pv-kicker">{t("profile.sellerBalanceTitle")}</p>
      <p className="mt-3 text-xs uppercase tracking-[0.2em] text-zinc-500">{t("profile.availableToPayout")}</p>
      <p className="mt-2 text-[2rem] font-bold leading-tight tracking-[-0.05em] text-zinc-950 sm:text-[2.65rem]">
        {formatDualCurrency(summary.available_balance_rub, summary.available_balance_lumens, locale)}
      </p>
      <p className="mt-2 text-sm text-zinc-600">{t("profile.nextPayoutDate", { date: nextPayoutDate })}</p>
      <p className="mt-1 text-xs text-zinc-500">
        {summary.payout_eligible ? t("profile.availableToPayoutReady") : t("profile.availableToPayoutEmpty")}
      </p>
      <div className="mt-5 flex flex-wrap gap-3">
        <Link href={APP_ROUTES.wallet} className="pv-button-primary !w-auto">
          {t("profile.withdrawFunds")}
        </Link>
        <Link href={APP_ROUTES.dashboard} className="pv-button-secondary !w-auto">
          {t("profile.openReport")}
        </Link>
      </div>
    </div>
  );
}

function MoneyStatusBlock({
  summary,
  payouts,
  purchases,
  locale,
}: {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
}) {
  const { t } = useI18n();
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);
  const pendingReleaseLabel = pendingReleaseDate
    ? t("profile.pendingReleaseAt", { date: formatDate(pendingReleaseDate, locale) })
    : t("profile.pendingReleaseNoDate");
  const holdRub = summary.clawback_due_rub + summary.disputed_balance_rub;
  const holdLumens = summary.clawback_due_lumens + summary.disputed_balance_lumens;
  const paidOutLast30 = formatPaidOutLast30(payouts, locale, t);

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <p className="pv-kicker">{t("profile.moneyStatusTitle")}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <StatusMetric
          title={t("profile.pendingStatus")}
          value={formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale)}
          caption={pendingReleaseLabel}
        />
        <StatusMetric
          title={t("profile.fees")}
          value={formatDualCurrency(summary.platform_commission_rub, summary.platform_commission_lumens, locale)}
        />
        <StatusMetric
          title={t("profile.holdsAndDisputes")}
          value={formatDualCurrency(holdRub, holdLumens, locale)}
          caption={`${t("profile.refunded")}: ${formatDualCurrency(summary.refunded_balance_rub, summary.refunded_balance_lumens, locale)}`}
        />
        <StatusMetric
          title={t("profile.paidOutLast30")}
          value={paidOutLast30.value}
          caption={paidOutLast30.caption}
        />
      </div>
    </div>
  );
}

function WhyZeroBalanceBlock({
  summary,
  purchases,
  locale,
}: {
  summary: SellerMarketplaceSummary;
  purchases: PromptMarketplacePurchase[];
  locale: string;
}) {
  const { t } = useI18n();
  const hasZeroAvailable = summary.available_balance_rub === 0 && summary.available_balance_lumens === 0;
  if (!hasZeroAvailable) {
    return null;
  }

  const reasons: string[] = [];
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);

  if (summary.pending_balance_rub !== 0 || summary.pending_balance_lumens !== 0) {
    const pendingAmount = formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale);
    reasons.push(
      pendingReleaseDate
        ? t("profile.zeroReasonPendingWithDate", { amount: pendingAmount, date: formatDate(pendingReleaseDate, locale) })
        : t("profile.zeroReasonPendingNoDate", { amount: pendingAmount }),
    );
  }

  const holdRub = summary.clawback_due_rub + summary.disputed_balance_rub;
  const holdLumens = summary.clawback_due_lumens + summary.disputed_balance_lumens;
  if (holdRub !== 0 || holdLumens !== 0) {
    reasons.push(t("profile.zeroReasonHoldDispute", { amount: formatDualCurrency(holdRub, holdLumens, locale) }));
  }

  if ((summary.platform_commission_rub !== 0 || summary.platform_commission_lumens !== 0) && reasons.length < 3) {
    reasons.push(
      t("profile.zeroReasonCommission", {
        amount: formatDualCurrency(summary.platform_commission_rub, summary.platform_commission_lumens, locale),
      }),
    );
  }

  const hasNoSales = summary.seller_revenue_rub === 0 && summary.seller_lumens_earned === 0;
  if (hasNoSales && reasons.length < 3) {
    reasons.push(t("profile.zeroReasonNoSales"));
  }

  if (reasons.length === 0) {
    reasons.push(t("profile.zeroReasonFallback"));
  }
  reasons.push(t("profile.zeroReasonPayoutRule"));

  return (
    <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-900">
      <p className="font-semibold">{t("profile.whyZeroBalance")}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5">
        {reasons.map((reason, index) => (
          <li key={`${reason}-${index}`}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

function MoneyPipeline({
  summary,
  payouts,
  purchases,
  locale,
}: {
  summary: SellerMarketplaceSummary;
  payouts: MarketplacePayout[];
  purchases: PromptMarketplacePurchase[];
  locale: string;
}) {
  const { t } = useI18n();
  const upcomingPayout = findUpcomingPayout(payouts);
  const latestPaidPayout = findLatestPaidPayout(payouts);
  const pendingReleaseDate = findNearestPendingSettlementDate(purchases);
  const steps: Array<{ label: string; amount: string; date?: string }> = [
    {
      label: t("profile.pipelinePaidByBuyers"),
      amount: formatDualCurrency(summary.seller_revenue_rub, summary.seller_lumens_earned, locale),
    },
    {
      label: t("profile.pipelineInHold"),
      amount: formatDualCurrency(summary.pending_balance_rub, summary.pending_balance_lumens, locale),
      date: pendingReleaseDate ? formatDate(pendingReleaseDate, locale) : undefined,
    },
    {
      label: t("profile.pipelineAvailable"),
      amount: formatDualCurrency(summary.available_balance_rub, summary.available_balance_lumens, locale),
    },
    {
      label: t("profile.pipelinePayout"),
      amount: upcomingPayout ? formatPayoutAmount(upcomingPayout, locale) : t("profile.pipelineNoPayoutQueue"),
      date: upcomingPayout ? formatDate(upcomingPayout.requested_at, locale) : undefined,
    },
    {
      label: t("profile.pipelinePaidOut"),
      amount: formatDualCurrency(summary.paid_out_rub, summary.paid_out_lumens, locale),
      date: latestPaidPayout?.paid_at ? formatDate(latestPaidPayout.paid_at, locale) : undefined,
    },
  ];

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <p className="pv-kicker">{t("profile.moneyPipelineTitle")}</p>
      <ol className="mt-4 space-y-3">
        {steps.map((step, index) => (
          <li key={`${step.label}-${index}`} className="relative rounded-[1rem] border border-zinc-200/80 bg-white p-3 pl-10">
            <span className="absolute left-4 top-4 h-2.5 w-2.5 rounded-full bg-[var(--pv-brand)]" aria-hidden="true" />
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{step.label}</p>
            <p className="mt-1 text-sm font-semibold text-zinc-900">{step.amount}</p>
            {step.date ? <p className="mt-1 text-xs text-zinc-500">{t("profile.pipelineDate", { date: step.date })}</p> : null}
          </li>
        ))}
      </ol>
    </div>
  );
}

function PayoutsTable({ payouts, locale }: { payouts: MarketplacePayout[]; locale: string }) {
  const { t } = useI18n();
  const sortedPayouts = [...payouts].sort((left, right) => Date.parse(right.requested_at) - Date.parse(left.requested_at));
  const upcomingPayout = findUpcomingPayout(payouts) ?? sortedPayouts[0] ?? null;

  return (
    <div className="rounded-[1.5rem] border border-zinc-200 bg-white/80 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="pv-kicker">{t("profile.recentPayouts")}</p>
          <p className="mt-1 text-sm text-zinc-600">{t("profile.recentPayoutsDescription")}</p>
        </div>
      </div>
      <div className="mt-4 rounded-[1rem] border border-zinc-200 bg-white p-4">
        <p className="text-xs uppercase tracking-[0.16em] text-zinc-500">{t("profile.nextPayoutCardTitle")}</p>
        {upcomingPayout ? (
          <>
            <p className="mt-2 text-lg font-semibold text-zinc-950">{formatPayoutAmount(upcomingPayout, locale)}</p>
            <p className="mt-1 text-sm text-zinc-600">
              {t("profile.nextPayoutCardDate", { date: formatDate(upcomingPayout.requested_at, locale) })}
            </p>
            <p className="mt-1 text-sm text-zinc-600">
              {t("profile.nextPayoutCardStatus", { status: humanizePayoutTableStatus(upcomingPayout.status, t) })}
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-zinc-500">{t("profile.noData")}</p>
        )}
      </div>
      {sortedPayouts.length ? (
        <div className="mt-4 overflow-x-auto rounded-[1rem] border border-zinc-200 bg-white">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50 text-left text-xs uppercase tracking-[0.14em] text-zinc-500">
                <th className="px-4 py-3">{t("profile.payoutsDateColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsAmountColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsStatusColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsMethodColumn")}</th>
                <th className="px-4 py-3">{t("profile.payoutsIdColumn")}</th>
              </tr>
            </thead>
            <tbody>
              {sortedPayouts.map((payout) => (
                <tr key={payout.id} className="border-b border-zinc-100 last:border-b-0">
                  <td className="px-4 py-3 text-zinc-700">{formatDate(payout.requested_at, locale)}</td>
                  <td className="px-4 py-3 font-medium text-zinc-900">{formatPayoutAmount(payout, locale)}</td>
                  <td className="px-4 py-3 text-zinc-700">{humanizePayoutTableStatus(payout.status, t)}</td>
                  <td className="px-4 py-3 text-zinc-600">{humanizePayoutMethod(payout.currency_code, t)}</td>
                  <td className="px-4 py-3 text-zinc-600">{payout.external_reference ?? payout.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-4 text-sm text-zinc-500">{t("profile.noPayouts")}</p>
      )}
    </div>
  );
}

function SellerTrustBlock({
  summary,
  ratingLabel,
  reviewsHref,
  publicReviewsHref,
}: {
  summary: SellerMarketplaceSummary;
  ratingLabel: string;
  reviewsHref: string;
  publicReviewsHref: string | null;
}) {
  const { t } = useI18n();

  return (
    <div className="rounded-[1.25rem] border border-zinc-200/80 bg-zinc-50/80 p-5 text-sm text-zinc-700">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">{t("profile.sellerTrustSecondaryKicker")}</p>
      <h3 className="mt-2 text-lg font-semibold text-zinc-900">{t("profile.sellerTrust")}</h3>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Link href={reviewsHref} className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-900">
          {summary.review_count > 0
            ? t("profile.ratingReviewsEntry", { rating: ratingLabel, count: summary.review_count })
            : t("profile.ratingReviewsEntryEmpty")}
        </Link>
        {publicReviewsHref ? (
          <Link href={publicReviewsHref} className="text-xs font-semibold text-[var(--pv-brand)]">
            {t("profile.openPublicReviewPage")}
          </Link>
        ) : null}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.averageRating")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{ratingLabel}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <Link href={reviewsHref} className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3 transition hover:border-zinc-300">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.verifiedReviews")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.review_count}</p>
          <p className="mt-1 text-xs text-zinc-500">{t("profile.openReviewsFromTrust")}</p>
        </Link>
        <div className="rounded-[0.9rem] border border-zinc-200/80 bg-white/70 p-3">
          <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("profile.promptsSold")}</p>
          <p className="mt-1 text-sm font-semibold text-zinc-900">{summary.sold_prompts_count}</p>
        </div>
      </div>
      <p className="mt-4 text-xs text-zinc-500">{t("profile.sellerTrustDescription")}</p>
      {summary.trust_indicators.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {summary.trust_indicators.map((indicator) => (
            <span key={indicator.key} className="pv-chip">
              {humanizeTrustIndicator(indicator.key, t)}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PurchaseReviewCard({
  locale,
  purchase,
  onSubmitted,
}: {
  locale: string;
  purchase: PromptMarketplacePurchase;
  onSubmitted: () => void;
}) {
  const { t } = useI18n();
  const [rating, setRating] = useState(purchase.review?.rating ?? 5);
  const [text, setText] = useState(purchase.review?.text ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    setRating(purchase.review?.rating ?? 5);
    setText(purchase.review?.text ?? "");
    setError(null);
    setSavedMessage(null);
  }, [purchase.id, purchase.review?.id, purchase.review?.rating, purchase.review?.text, purchase.review?.updated_at]);

  async function submit() {
    if (!purchase.can_review) {
      return;
    }

    setError(null);
    setSavedMessage(null);
    setPending(true);
    try {
      await upsertPromptReview(purchase.prompt_id, { rating, text: text.trim() || null });
      setSavedMessage(purchase.review ? t("profile.reviewUpdated") : t("profile.reviewSaved"));
      onSubmitted();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("profile.reviewSaveFailed"));
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="rounded-[1rem] border border-zinc-200 bg-white/75 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href={appRoute.promptBySlug(purchase.prompt_slug)} className="font-semibold text-zinc-900 underline">
            {purchase.prompt_title}
          </Link>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-500">
            <span className="pv-chip">
              {purchase.price_rub > 0
                ? `${formatNumber(purchase.price_rub, locale)} RUB`
                : `${formatNumber(purchase.price_lumens, locale)} LMN`}
            </span>
            <span className="pv-chip">{humanizePaymentMethod(purchase.payment_method, t)}</span>
            <span className={purchase.status === "completed" ? "pv-chip" : "pv-badge-warning"}>
              {humanizePurchaseStatus(purchase.status, t)}
            </span>
            {purchase.settlement_status ? (
              <span className={purchase.settlement_status === "available" || purchase.settlement_status === "paid_out" ? "pv-chip" : "pv-badge-warning"}>
                {humanizeSettlementStatus(purchase.settlement_status, t)}
              </span>
            ) : null}
          </div>
          <p className="mt-3 text-xs text-zinc-500">
            {t("profile.purchaseDate", { date: formatDate(purchase.completed_at ?? purchase.created_at, locale) })}
          </p>
          {purchase.settlement_status === "pending" && purchase.settlement_available_at ? (
            <p className="mt-2 text-xs text-zinc-500">
              {t("profile.sellerSettlementRelease", { date: formatDate(purchase.settlement_available_at, locale) })}
            </p>
          ) : null}
          {purchase.review ? (
            <>
              <p className="mt-2 text-xs text-zinc-500">
                {t("profile.lastReviewUpdate", { date: formatDate(purchase.review.updated_at, locale) })}
              </p>
              <p className="mt-2 text-xs text-zinc-500">
                {t("profile.reviewState", {
                  status: humanizeReviewModerationStatus(purchase.review.moderation_status, t),
                })}
                {purchase.review.moderation_reason
                  ? ` · ${humanizeReviewModerationReason(purchase.review.moderation_reason, t)}`
                  : ""}
              </p>
            </>
          ) : null}
        </div>

        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setRating(value)}
              disabled={!purchase.can_review}
              className={value <= rating ? "pv-button-secondary disabled:opacity-60" : "pv-chip disabled:opacity-60"}
            >
              {value}
            </button>
          ))}
        </div>
      </div>

      {purchase.can_review ? (
        <>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={4}
            className="pv-textarea mt-3"
            placeholder={t("profile.reviewPlaceholder")}
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button type="button" onClick={() => void submit()} disabled={pending} className="pv-button-primary disabled:opacity-60">
              {pending ? t("profile.saving") : purchase.review ? t("profile.updateReview") : t("profile.saveReview")}
            </button>
            {savedMessage ? <span className="text-sm text-emerald-700">{savedMessage}</span> : null}
            {error ? <span className="text-sm text-red-700">{error}</span> : null}
          </div>
          {purchase.review?.moderation_status === "pending" ? (
            <p className="mt-3 text-sm text-amber-700">
              {t("profile.reviewPendingModeration")}
            </p>
          ) : null}
          {purchase.review?.moderation_status === "hidden" ? (
            <p className="mt-3 text-sm text-zinc-600">
              {t("profile.reviewHiddenNotice")}
            </p>
          ) : null}
        </>
      ) : (
        <p className="mt-3 text-sm text-zinc-600">
          {purchase.status === "refunded"
            ? t("profile.refundedPurchasesNoReviews")
            : purchase.status === "completed"
              ? t("profile.reviewAvailableWhenAttached")
            : t("profile.reviewAvailableForCompleted")}
        </p>
      )}
    </div>
  );
}

function humanizeTrustIndicator(key: string, t: TranslateFn): string {
  return TRUST_INDICATOR_LABELS[key] ? t(TRUST_INDICATOR_LABELS[key]) : humanizeSnakeCase(key);
}

function humanizePaymentMethod(value: PromptMarketplacePurchase["payment_method"], t: TranslateFn): string {
  return t(PAYMENT_METHOD_LABELS[value]);
}

function humanizePurchaseStatus(status: PromptMarketplacePurchase["status"], t: TranslateFn): string {
  return t(PURCHASE_STATUS_LABELS[status]);
}

function humanizeSettlementStatus(status: PromptMarketplacePurchase["settlement_status"], t: TranslateFn): string {
  if (!status) {
    return t("profile.settlementStatusPending");
  }
  return t(SETTLEMENT_STATUS_LABELS[status]);
}

function humanizePayoutStatus(status: MarketplacePayout["status"], t: TranslateFn): string {
  return t(PAYOUT_STATUS_LABELS[status]);
}

function humanizePayoutTableStatus(status: MarketplacePayout["status"], t: TranslateFn): string {
  switch (status) {
    case "requested":
      return t("profile.payoutTableStatusProcessing");
    case "processing":
      return t("profile.payoutTableStatusSent");
    case "paid":
      return t("profile.payoutTableStatusCredited");
    case "failed":
    case "canceled":
      return t("profile.payoutTableStatusError");
    default:
      return humanizePayoutStatus(status, t);
  }
}

function humanizePayoutMethod(currencyCode: string, t: TranslateFn): string {
  const normalized = currencyCode.toUpperCase();
  if (normalized === "LMN") {
    return t("profile.payoutMethodLmn");
  }
  if (normalized === "RUB") {
    return t("profile.payoutMethodRub");
  }
  return t("profile.payoutMethodUnknown");
}

function formatPaidOutLast30(
  payouts: MarketplacePayout[],
  locale: string,
  t: TranslateFn,
): { value: string; caption: string | undefined } {
  if (payouts.length === 0) {
    return {
      value: `${formatNumber(0, locale)} RUB`,
      caption: t("profile.paidOutLast30NoCompleted"),
    };
  }

  const now = Date.now();
  const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000;
  const totalsByCurrency = new Map<string, number>();

  for (const payout of payouts) {
    if (payout.status !== "paid") {
      continue;
    }
    const referenceDate = payout.paid_at ?? payout.requested_at;
    const timestamp = Date.parse(referenceDate);
    if (!Number.isFinite(timestamp) || now - timestamp > thirtyDaysMs) {
      continue;
    }
    const code = payout.currency_code.toUpperCase();
    totalsByCurrency.set(code, (totalsByCurrency.get(code) ?? 0) + payout.total_amount);
  }

  if (totalsByCurrency.size === 0) {
    const fallbackCurrency = payouts[0]?.currency_code?.toUpperCase() ?? "RUB";
    return {
      value: `${formatNumber(0, locale)} ${fallbackCurrency}`,
      caption: t("profile.paidOutLast30NoCompleted"),
    };
  }

  const value = [...totalsByCurrency.entries()]
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([currency, amount]) => `${formatNumber(amount, locale)} ${currency}`)
    .join(" · ");
  return { value, caption: undefined };
}

function findUpcomingPayout(payouts: MarketplacePayout[]): MarketplacePayout | null {
  const activeStatuses: MarketplacePayout["status"][] = ["requested", "processing"];
  const active = payouts.filter((payout) => activeStatuses.includes(payout.status));
  if (!active.length) {
    return null;
  }
  return [...active].sort((left, right) => Date.parse(left.requested_at) - Date.parse(right.requested_at))[0] ?? null;
}

function findLatestPaidPayout(payouts: MarketplacePayout[]): MarketplacePayout | null {
  const paid = payouts.filter((payout) => payout.status === "paid" && payout.paid_at);
  if (!paid.length) {
    return null;
  }
  return [...paid].sort((left, right) => Date.parse(right.paid_at ?? right.requested_at) - Date.parse(left.paid_at ?? left.requested_at))[0] ?? null;
}

function findNearestPendingSettlementDate(purchases: PromptMarketplacePurchase[]): string | null {
  const withDate = purchases
    .filter((purchase) => purchase.settlement_status === "pending" && purchase.settlement_available_at)
    .map((purchase) => ({
      date: purchase.settlement_available_at as string,
      timestamp: Date.parse(purchase.settlement_available_at as string),
    }))
    .filter((value) => Number.isFinite(value.timestamp))
    .sort((left, right) => left.timestamp - right.timestamp);
  if (!withDate.length) {
    return null;
  }
  return withDate[0].date;
}

function humanizeReviewModerationStatus(
  status: PromptReview["moderation_status"] | null | undefined,
  t: TranslateFn,
): string {
  return t(REVIEW_MODERATION_STATUS_LABELS[status ?? "visible"]);
}

function humanizeReviewModerationReason(reason: string, t: TranslateFn): string {
  return REVIEW_MODERATION_REASON_LABELS[reason]
    ? t(REVIEW_MODERATION_REASON_LABELS[reason])
    : humanizeSnakeCase(reason);
}

function renderRating(value: number | null | undefined, emptyLabel: string): string {
  if (!value) {
    return emptyLabel;
  }
  const rounded = Math.max(1, Math.min(5, Math.round(value)));
  return `${"★".repeat(rounded)}${"☆".repeat(5 - rounded)} ${value.toFixed(1)}`;
}

function formatDualCurrency(rub: number, lumens: number, locale: string): string {
  const parts: string[] = [];
  if (rub !== 0 || (rub === 0 && lumens === 0)) {
    parts.push(`${formatNumber(rub, locale)} RUB`);
  }
  if (lumens !== 0) {
    parts.push(`${formatNumber(lumens, locale)} LMN`);
  }
  return parts.join(" · ");
}

function formatPayoutAmount(payout: MarketplacePayout, locale: string): string {
  return `${formatNumber(payout.total_amount, locale)} ${payout.currency_code.toUpperCase()}`;
}

function formatDateTime(value: string, locale: string): string {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(parsed));
}
