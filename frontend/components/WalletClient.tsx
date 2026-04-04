"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { BestNextPurchase } from "@/components/wallet/BestNextPurchase";
import { KPIStrip } from "@/components/wallet/KPIStrip";
import { ProgressAndRewards } from "@/components/wallet/ProgressAndRewards";
import { useWalletData } from "@/components/wallet/useWalletData";
import { APP_ROUTES } from "@/lib/constants/routes";
import {
  buildDailyLadder,
  nextMilestone,
  pickBestStoreItem,
  resolveStreakMilestones,
} from "@/lib/economy";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDateTime, formatMultiplier, formatNumber } from "@/lib/formatters";
import { languageToIntlLocale } from "@/lib/i18n";
import type { CurrencyTransaction, WalletPurchase } from "@/lib/types";
import {
  benefitKindLabel,
  benefitLabel,
  benefitMetaLines,
  estimateDaysToAfford,
  formatSignedAmount,
  localizedGoalCopy,
  reasonLabel,
} from "@/components/wallet/walletPresentation";

export function WalletClient() {
  const { status } = useAuth();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const {
    wallet,
    items,
    error,
    loading,
    checkinPending,
    checkinFeedback,
    reload,
    checkIn,
  } = useWalletData({
    status,
    genericErrorMessage: t("wallet.checkInError"),
  });
  const [activityPage, setActivityPage] = useState(1);
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);

  useEffect(() => {
    setActivityPage(1);
  }, [wallet?.recent.length]);

  async function handleCheckIn() {
    await checkIn();
  }

  if (status === "loading" || loading) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("economy.loopBody")}
        />
        <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("wallet.guestHint")}
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("wallet.signInPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
            {t("wallet.signInLink")}
          </Link>{" "}
          {t("wallet.signInSuffix")}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("economy.loopBody")}
        />
        <div className="pv-alert pv-alert-warning space-y-3">
          <p>{error}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={reload}
              className="pv-button-secondary !w-auto"
            >
              {t("wallet.refresh")}
            </button>
            <button type="button" onClick={handleCheckIn} className="pv-button-primary !w-auto">
              {t("wallet.checkinCta")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  const activityPageSize = 10;
  const totalActivityPages = Math.max(1, Math.ceil(wallet.recent.length / activityPageSize));
  const currentActivityPage = Math.min(activityPage, totalActivityPages);
  const activityStart = (currentActivityPage - 1) * activityPageSize;
  const pagedRecent = wallet.recent.slice(activityStart, activityStart + activityPageSize);
  const checkInMessage = wallet.check_in_available
    ? t("wallet.checkinReady")
    : `${t("wallet.checkinLocked")}${wallet.last_check_in_at ? ` · ${formatDateTime(wallet.last_check_in_at, locale)}` : ""}`;
  const bestItem = pickBestStoreItem(items);
  const readyToBuyCount = items.filter(
    (item) => !item.owned && item.is_affordable && (item.availability === null || item.availability > 0),
  ).length;
  const ladder = buildDailyLadder(wallet.current_streak, wallet);
  const streakMilestones = resolveStreakMilestones(wallet);
  const nextMilestoneEntry = nextMilestone(wallet.current_streak, wallet);
  const pendingCashbackTotal = wallet.pending_locked_rewards.reduce((sum, reward) => sum + reward.amount, 0);
  const estimatedDaysToAfford = estimateDaysToAfford(bestItem, ladder, wallet.spend_streak_mult);

  return (
    <div className="space-y-6">
      <EconomyActionBanner summary={checkinFeedback} />

      <PageIntro
        breadcrumbs={[
          { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
          { label: t("nav.economy") },
          { label: t("nav.wallet") },
        ]}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={
          bestItem
            ? bestItem.is_affordable
              ? t("wallet.bestUseReady", { title: bestItem.title })
              : t("wallet.bestUseAlmost", { title: bestItem.title, count: bestItem.remaining_lumens })
            : checkInMessage
        }
        actions={
          <>
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={checkinPending || !wallet.check_in_available}
              className="pv-button-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {checkinPending ? t("missions.loading") : t("wallet.checkinCta")}
            </button>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="sm:col-span-3 xl:col-span-1">
              <LmnBalanceCard
                label={t("wallet.balance")}
                amount={wallet.balance}
                symbol={TOKEN_SHORT_CODE}
                caption={t("wallet.currencyHint")}
                detail={wallet.check_in_available ? t("wallet.checkinReady") : t("wallet.checkinLocked")}
                delta={balanceDelta}
                change={balanceChange}
                showIcon
                compactCode={false}
              />
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.currentStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{wallet.current_streak}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.spendStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {t("wallet.spendStreakValue", {
                  days: formatNumber(wallet.spend_streak_days, locale),
                  mult: formatMultiplier(wallet.spend_streak_mult, locale),
                })}
              </p>
            </div>
          </div>
        }
      />

      <div className="mx-auto grid w-full max-w-[1280px] grid-cols-12 gap-4 px-6 lg:items-start">
        <div className="col-span-12 lg:col-span-7">
          <BestNextPurchase
            bestItem={bestItem}
            balance={wallet.balance}
            estimatedDaysToAfford={estimatedDaysToAfford}
          />
        </div>
        <div className="col-span-12 lg:col-span-5">
          <ProgressAndRewards
            ladder={ladder}
            streakMilestones={streakMilestones}
            currentStreak={wallet.current_streak}
            nextMilestone={nextMilestoneEntry}
            rankLevel={wallet.rank_level}
            rankPoints={wallet.rank_points}
            rankNextThreshold={wallet.rank_next_threshold}
            ownedValueGenerated={wallet.owned_value_generated}
          />
        </div>
        <div className="col-span-12">
          <KPIStrip
            earned={wallet.total_earned}
            spent={wallet.total_spent}
            readyToBuy={readyToBuyCount}
            purchases={wallet.recent_purchases.length}
            cashback={pendingCashbackTotal}
          />
        </div>
      </div>

      {wallet.goals.length > 0 ? (
        <section className="pv-panel px-5 py-5">
          <p className="pv-kicker">{t("wallet.activeGoals")}</p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {wallet.goals.map((goal) => {
              const localizedGoal = localizedGoalCopy(goal, t);
              return (
                <div key={goal.key} className="pv-card-muted p-4">
                  <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{localizedGoal.layer}</p>
                  <p className="mt-2 text-sm font-semibold text-zinc-900">{localizedGoal.title}</p>
                  <p className="mt-1 text-xs text-zinc-600">{localizedGoal.description}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    {formatNumber(goal.progress, locale)}/{formatNumber(goal.target, locale)}
                  </p>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:items-start">
        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.benefitsAndBoosts")}</h2>
            </div>
            <LmnAmount amount={wallet.balance} symbol={TOKEN_SHORT_CODE} strong state="balance" />
          </div>
          {wallet.active_benefits.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noBenefits")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.active_benefits.map((benefit) => {
                const metaLines = benefitMetaLines(benefit, t, locale);
                return (
                  <div key={benefit.key} className="pv-card-muted p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-zinc-900">{benefitLabel(benefit, t, locale)}</p>
                        {metaLines.map((line, index) => (
                          <p key={`${benefit.key}-meta-${index}`} className="mt-1 text-xs text-zinc-500">
                            {line}
                          </p>
                        ))}
                        {typeof benefit.metadata?.reward_body === "string" ? (
                          <p className="mt-2 text-xs text-zinc-600">{String(benefit.metadata.reward_body)}</p>
                        ) : null}
                      </div>
                      <span className="pv-badge-brand">{benefitKindLabel(benefit.kind, t)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {wallet.pending_locked_rewards.length > 0 ? (
            <div className="mt-5 space-y-3">
              {wallet.pending_locked_rewards.map((reward) => (
                <div key={reward.id} className="pv-card-muted p-4">
                  <p className="text-sm font-semibold text-zinc-900">
                    {t("wallet.pendingCashbackLocked", { amount: formatNumber(reward.amount, locale) })}
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    {t("wallet.pendingCashbackMissions", {
                      completed: formatNumber(reward.completed_mission_count, locale),
                      required: formatNumber(reward.required_mission_count, locale),
                    })}
                    {reward.unlock_by
                      ? ` · ${t("wallet.pendingCashbackUnlockBy", {
                          date: formatDateTime(reward.unlock_by, locale),
                        })}`
                      : ""}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
        </section>

        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.latestPurchases")}</h2>
            </div>
            <Link href={APP_ROUTES.store} className="pv-inline-link">
              {t("nav.store")}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
          {wallet.recent_purchases.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noPurchases")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.recent_purchases.map((purchase: WalletPurchase) => (
                <div key={purchase.id} className="pv-card-muted p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{purchase.item_title}</p>
                      <p className="mt-1 text-xs text-zinc-500">{formatDateTime(purchase.created_at, locale)}</p>
                    </div>
                    <LmnAmount amount={`-${purchase.price_paid}`} symbol={TOKEN_SHORT_CODE} state="spent" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="pv-panel px-5 py-5">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <p className="pv-kicker">{t("wallet.operationsTimeline")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.operationsTimeline")}</h2>
          </div>
          <LmnAmount amount={wallet.balance} symbol={TOKEN_SHORT_CODE} state="balance" />
        </div>

        {wallet.recent.length === 0 ? (
          <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.empty")}</div>
        ) : (
          <div className="mt-5 space-y-3">
            {pagedRecent.map((tx: CurrencyTransaction) => (
              <div key={tx.id} className="pv-card-muted p-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-1 h-2.5 w-2.5 rounded-full ${
                        tx.amount > 0 ? "bg-[var(--pv-success)]" : "bg-slate-400"
                      }`}
                    />
                    <div>
                      <p className="font-semibold text-zinc-900">{reasonLabel(tx.reason, t)}</p>
                      <p className="text-xs text-zinc-500">
                        {formatDateTime(tx.created_at, locale)}
                        {tx.context ? ` · ${tx.context}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <LmnAmount
                      amount={formatSignedAmount(tx.amount)}
                      symbol={TOKEN_SHORT_CODE}
                      state={tx.amount > 0 ? "earned" : "spent"}
                      className="pv-lmn-token-no-border"
                    />
                    <p className="mt-2 text-xs text-zinc-500">
                      {t("wallet.balance")}: {tx.balance_after}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {wallet.recent.length > activityPageSize ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setActivityPage((value) => Math.max(1, value - 1))}
              disabled={currentActivityPage <= 1}
              className="pv-button-secondary !w-auto disabled:opacity-60"
            >
              {t("wallet.prevPage")}
            </button>
            <p className="text-sm text-zinc-600">
              {t("wallet.pageCounter", { current: currentActivityPage, total: totalActivityPages })}
            </p>
            <button
              type="button"
              onClick={() => setActivityPage((value) => Math.min(totalActivityPages, value + 1))}
              disabled={currentActivityPage >= totalActivityPages}
              className="pv-button-secondary !w-auto disabled:opacity-60"
            >
              {t("wallet.nextPage")}
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
