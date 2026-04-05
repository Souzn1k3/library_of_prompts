"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  buildDailyLadder,
  nextMilestone,
  pickBestStoreItem,
  resolveStreakMilestones,
} from "@/lib/economy";
import { formatDateTime } from "@/lib/formatters";
import type { StoreItem, WalletRead } from "@/lib/types";
import { estimateDaysToAfford, type WalletTranslate } from "@/components/wallet/walletPresentation";

const ACTIVITY_PAGE_SIZE = 10;

type UseWalletViewModelArgs = {
  wallet: WalletRead | null;
  items: StoreItem[];
  locale: string;
  t: WalletTranslate;
};

export function useWalletViewModel({ wallet, items, locale, t }: UseWalletViewModelArgs) {
  const [activityPage, setActivityPage] = useState(1);
  const recentTransactions = useMemo(() => wallet?.recent ?? [], [wallet?.recent]);

  useEffect(() => {
    setActivityPage(1);
  }, [recentTransactions.length]);

  const bestItem = useMemo(() => pickBestStoreItem(items), [items]);

  const readyToBuyCount = useMemo(
    () =>
      items.filter(
        (item) =>
          !item.owned &&
          item.is_affordable &&
          (item.availability === null || item.availability > 0),
      ).length,
    [items],
  );

  const ladder = useMemo(
    () => (wallet ? buildDailyLadder(wallet.current_streak, wallet) : []),
    [wallet],
  );
  const streakMilestones = useMemo(() => resolveStreakMilestones(wallet ?? undefined), [wallet]);
  const nextMilestoneEntry = useMemo(
    () => (wallet ? nextMilestone(wallet.current_streak, wallet) : null),
    [wallet],
  );

  const pendingCashbackTotal = useMemo(
    () => (wallet ? wallet.pending_locked_rewards.reduce((sum, reward) => sum + reward.amount, 0) : 0),
    [wallet],
  );

  const estimatedDaysToAfford = useMemo(
    () => estimateDaysToAfford(bestItem, ladder, wallet?.spend_streak_mult ?? 1),
    [bestItem, ladder, wallet?.spend_streak_mult],
  );

  const checkInMessage = useMemo(
    () => {
      if (!wallet) {
        return t("wallet.checkinReady");
      }
      return (
      wallet.check_in_available
        ? t("wallet.checkinReady")
        : `${t("wallet.checkinLocked")}${
            wallet.last_check_in_at
              ? ` · ${formatDateTime(wallet.last_check_in_at, locale)}`
              : ""
          }`
      );
    },
    [locale, t, wallet],
  );

  const totalActivityPages = useMemo(
    () => Math.max(1, Math.ceil(recentTransactions.length / ACTIVITY_PAGE_SIZE)),
    [recentTransactions.length],
  );

  const currentActivityPage = Math.min(activityPage, totalActivityPages);

  const pagedRecent = useMemo(() => {
    const startIndex = (currentActivityPage - 1) * ACTIVITY_PAGE_SIZE;
    return recentTransactions.slice(startIndex, startIndex + ACTIVITY_PAGE_SIZE);
  }, [currentActivityPage, recentTransactions]);

  const goToPreviousActivityPage = useCallback(() => {
    setActivityPage((value) => Math.max(1, value - 1));
  }, []);

  const goToNextActivityPage = useCallback(() => {
    setActivityPage((value) => Math.min(totalActivityPages, value + 1));
  }, [totalActivityPages]);

  return {
    bestItem,
    readyToBuyCount,
    ladder,
    streakMilestones,
    nextMilestoneEntry,
    pendingCashbackTotal,
    estimatedDaysToAfford,
    checkInMessage,
    activityPageSize: ACTIVITY_PAGE_SIZE,
    totalActivityPages,
    currentActivityPage,
    pagedRecent,
    goToPreviousActivityPage,
    goToNextActivityPage,
  };
}
