import { formatNumber } from "@/lib/formatters";
import type { TranslationKey } from "@/lib/i18n";
import type { StoreItem, WalletRead } from "@/lib/types";

import type { WalletTranslate } from "./walletPresentationTypes";

export function localizedGoalCopy(
  goal: WalletRead["goals"][number],
  t: WalletTranslate,
): { layer: string; title: string; description: string } {
  const layerKey = `wallet.goal.layer.${goal.layer}` as TranslationKey;
  const translatedLayer = t(layerKey);
  const layer = translatedLayer === layerKey ? goal.layer : translatedLayer;

  const slugOrLevel = goal.key.includes(":") ? goal.key.split(":")[1] : null;
  const titleSuffix = goal.title.includes(":") ? goal.title.split(":").slice(1).join(":").trim() : "";
  const fallbackTitle = titleSuffix || slugOrLevel?.replaceAll("-", " ") || goal.title;

  if (goal.key.startsWith("next-item:")) {
    return {
      layer,
      title: t("wallet.goal.nextUnlockTitle", { title: fallbackTitle }),
      description: t("wallet.goal.nextUnlockDescription"),
    };
  }
  if (goal.key.startsWith("buy-now:")) {
    return {
      layer,
      title: t("wallet.goal.buyNowTitle", { title: fallbackTitle }),
      description: t("wallet.goal.buyNowDescription"),
    };
  }
  if (goal.key === "next-earn") {
    return {
      layer,
      title: t("wallet.goal.nextEarnTitle"),
      description: t("wallet.goal.nextEarnDescription"),
    };
  }
  if (goal.key.startsWith("inactive-comeback:")) {
    return {
      layer,
      title: t("wallet.goal.comebackTitle", { count: goal.target }),
      description: t("wallet.goal.comebackDescription"),
    };
  }
  if (goal.key.startsWith("hoarder-convert:")) {
    return {
      layer,
      title: t("wallet.goal.hoarderTitle", { count: goal.target }),
      description: t("wallet.goal.hoarderDescription"),
    };
  }
  if (goal.key.startsWith("spender-maintain:")) {
    return {
      layer,
      title: t("wallet.goal.spenderTitle", { count: goal.target }),
      description: t("wallet.goal.spenderDescription"),
    };
  }
  if (goal.key.startsWith("habit-window:")) {
    return {
      layer,
      title: t("wallet.goal.habitTitle", { count: goal.target }),
      description: t("wallet.goal.habitDescription"),
    };
  }
  if (goal.key.startsWith("rank:")) {
    const level = slugOrLevel ?? String(goal.target);
    return {
      layer,
      title: t("wallet.goal.rankTitle", { level }),
      description: t("wallet.goal.rankDescription"),
    };
  }
  return {
    layer,
    title: goal.title || t("wallet.goal.unknown"),
    description: goal.description,
  };
}

export function estimateDaysToAfford(
  bestItem: StoreItem | null,
  ladder: Array<{ reward: number }>,
  spendStreakMultiplier: number,
): number | null {
  if (!bestItem || bestItem.is_affordable || bestItem.remaining_lumens <= 0) {
    return null;
  }

  const totalReward = ladder.reduce((sum, step) => sum + Math.max(step.reward, 0), 0);
  const averageReward = ladder.length > 0 ? totalReward / ladder.length : 0;
  const projectedDailyReward = Math.max(1, averageReward * Math.max(spendStreakMultiplier, 1));
  return Math.max(1, Math.ceil(bestItem.remaining_lumens / projectedDailyReward));
}

export function formatLocalizedGoalProgress(
  value: number,
  target: number,
  locale: string,
): string {
  return `${formatNumber(value, locale)}/${formatNumber(target, locale)}`;
}
