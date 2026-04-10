"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { BestNextPurchase } from "@/components/wallet/BestNextPurchase";
import { ProgressAndRewards } from "@/components/wallet/ProgressAndRewards";
import { WalletActivitySection } from "@/components/wallet/WalletActivitySection";
import { WalletBenefitsSection } from "@/components/wallet/WalletBenefitsSection";
import { WalletGoalsSection } from "@/components/wallet/WalletGoalsSection";
import { WalletHero } from "@/components/wallet/WalletHero";
import { WalletPurchasesSection } from "@/components/wallet/WalletPurchasesSection";
import {
  WalletErrorView,
  WalletLoadingView,
  WalletUnauthenticatedView,
} from "@/components/wallet/WalletStatusViews";
import { useWalletData } from "@/components/wallet/useWalletData";
import { useWalletViewModel } from "@/components/wallet/useWalletViewModel";
import { APP_ROUTES } from "@/lib/constants/routes";
import { languageToIntlLocale } from "@/lib/i18n";
import {
  type WalletTranslate,
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
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);

  const walletT: WalletTranslate = t;
  const breadcrumbs = [
    { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
    { label: t("nav.economy") },
    { label: t("nav.wallet") },
  ];
  const handleCheckIn = () => checkIn();
  const walletViewModel = useWalletViewModel({
    wallet,
    items,
    locale,
    t: walletT,
  });

  if (status === "loading" || loading) {
    return <WalletLoadingView breadcrumbs={breadcrumbs} t={walletT} />;
  }

  if (status === "unauthenticated") {
    return <WalletUnauthenticatedView breadcrumbs={breadcrumbs} t={walletT} />;
  }

  if (error) {
    return (
      <WalletErrorView
        breadcrumbs={breadcrumbs}
        t={walletT}
        error={error}
        onReload={reload}
        onCheckIn={handleCheckIn}
      />
    );
  }

  if (!wallet) return null;

  const {
    bestItem,
    readyToBuyCount,
    ladder,
    streakMilestones,
    nextMilestoneEntry,
    pendingCashbackTotal,
    estimatedDaysToAfford,
    checkInMessage,
    activityPageSize,
    totalActivityPages,
    currentActivityPage,
    pagedRecent,
    goToPreviousActivityPage,
    goToNextActivityPage,
  } = walletViewModel;

  return (
    <div className="space-y-6">
      <EconomyActionBanner summary={checkinFeedback} />

      <WalletHero
        breadcrumbs={breadcrumbs}
        t={walletT}
        locale={locale}
        wallet={wallet}
        checkinPending={checkinPending}
        onCheckIn={handleCheckIn}
        bestItem={bestItem}
        checkInMessage={checkInMessage}
        balanceChange={balanceChange}
        balanceDelta={balanceDelta}
      />

      <div className="mx-auto grid w-full max-w-[1280px] grid-cols-12 gap-4 px-6 lg:items-start">
        <div className="col-span-12 lg:col-span-7">
          <BestNextPurchase
            bestItem={bestItem}
            balance={wallet.balance}
            estimatedDaysToAfford={estimatedDaysToAfford}
            earned={wallet.total_earned}
            spent={wallet.total_spent}
            readyToBuy={readyToBuyCount}
            purchases={wallet.recent_purchases.length}
            cashback={pendingCashbackTotal}
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
      </div>

      <WalletGoalsSection goals={wallet.goals} locale={locale} t={walletT} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:items-start">
        <WalletBenefitsSection
          balance={wallet.balance}
          activeBenefits={wallet.active_benefits}
          pendingLockedRewards={wallet.pending_locked_rewards}
          locale={locale}
          t={walletT}
        />
        <WalletPurchasesSection purchases={wallet.recent_purchases} locale={locale} t={walletT} />
      </div>

      <WalletActivitySection
        balance={wallet.balance}
        allTransactions={wallet.recent}
        pagedTransactions={pagedRecent}
        activityPageSize={activityPageSize}
        currentActivityPage={currentActivityPage}
        totalActivityPages={totalActivityPages}
        onPreviousPage={goToPreviousActivityPage}
        onNextPage={goToNextActivityPage}
        locale={locale}
        t={walletT}
      />
    </div>
  );
}
