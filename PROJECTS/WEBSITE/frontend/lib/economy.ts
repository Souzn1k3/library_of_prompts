import type { EconomyAction, StoreItem, WalletRead } from "./types";

export const DEFAULT_DAILY_LADDER_REWARDS = [2, 2, 3, 3, 4, 4, 8] as const;
export const DEFAULT_STREAK_MILESTONES = [
  { streak: 3, reward: 2 },
  { streak: 7, reward: 4 },
  { streak: 14, reward: 8 },
  { streak: 30, reward: 16 },
] as const;
export const STREAK_MILESTONES = DEFAULT_STREAK_MILESTONES;

type WalletEconomyProjection = Pick<WalletRead, "economy_config">;

function hasValidMilestones(
  value: WalletRead["economy_config"] | null | undefined,
): value is NonNullable<WalletRead["economy_config"]> {
  return (
    !!value &&
    Array.isArray(value.streak_milestones) &&
    value.streak_milestones.every(
      (item) =>
        item &&
        typeof item.streak === "number" &&
        Number.isFinite(item.streak) &&
        typeof item.reward === "number" &&
        Number.isFinite(item.reward),
    )
  );
}

function hasValidLadder(
  value: WalletRead["economy_config"] | null | undefined,
): value is NonNullable<WalletRead["economy_config"]> {
  return (
    !!value &&
    Array.isArray(value.daily_ladder_rewards) &&
    value.daily_ladder_rewards.every((item) => typeof item === "number" && Number.isFinite(item))
  );
}

export function resolveDailyLadderRewards(wallet?: WalletEconomyProjection | null): readonly number[] {
  const config = wallet?.economy_config;
  if (hasValidLadder(config) && config.daily_ladder_rewards.length > 0) {
    return config.daily_ladder_rewards;
  }
  return DEFAULT_DAILY_LADDER_REWARDS;
}

export function resolveStreakMilestones(
  wallet?: WalletEconomyProjection | null,
): ReadonlyArray<{ streak: number; reward: number }> {
  const config = wallet?.economy_config;
  if (hasValidMilestones(config) && config.streak_milestones.length > 0) {
    return config.streak_milestones;
  }
  return DEFAULT_STREAK_MILESTONES;
}

function isAvailable(item: StoreItem) {
  return item.is_active && !item.owned && (item.availability === null || item.availability > 0);
}

export function sortStoreItems(items: StoreItem[]) {
  return [...items].sort((left, right) => {
    if (left.price !== right.price) {
      return left.price - right.price;
    }
    return left.title.localeCompare(right.title);
  });
}

export function getAffordableStoreItems(items: StoreItem[]) {
  return sortStoreItems(items.filter((item) => isAvailable(item) && item.is_affordable));
}

export function getNearMissStoreItems(items: StoreItem[], limit = 3) {
  return sortStoreItems(
    items.filter((item) => isAvailable(item) && !item.is_affordable && item.remaining_lumens > 0),
  ).slice(0, limit);
}

export function pickBestStoreItem(items: StoreItem[]) {
  const availableItems = sortStoreItems(items.filter(isAvailable));
  if (availableItems.length === 0) {
    return null;
  }

  const affordable = availableItems.filter((item) => item.is_affordable);
  if (affordable.length > 0) {
    return [...affordable].sort((left, right) => {
      if (left.tags.includes("starter") !== right.tags.includes("starter")) {
        return left.tags.includes("starter") ? -1 : 1;
      }
      return left.price - right.price;
    })[0];
  }

  return [...availableItems].sort((left, right) => {
    if (left.remaining_lumens !== right.remaining_lumens) {
      return left.remaining_lumens - right.remaining_lumens;
    }
    return left.price - right.price;
  })[0];
}

export function currentLadderDay(streak: number) {
  const ladderRewards = DEFAULT_DAILY_LADDER_REWARDS;
  if (streak <= 0) {
    return 1;
  }
  return ((streak - 1) % ladderRewards.length) + 1;
}

export function buildDailyLadder(streak: number, wallet?: WalletEconomyProjection | null) {
  const ladderRewards = resolveDailyLadderRewards(wallet);
  const activeDay = streak > 0 ? ((streak - 1) % ladderRewards.length) + 1 : 0;
  return ladderRewards.map((reward, index) => ({
    day: index + 1,
    reward,
    isActive: activeDay === index + 1,
    isComplete: streak > index,
    isBigReward: index === ladderRewards.length - 1,
  }));
}

export function nextMilestone(streak: number, wallet?: WalletEconomyProjection | null) {
  return resolveStreakMilestones(wallet).find((item) => item.streak > streak) ?? null;
}

export function buildClientEconomyAction(params: {
  balanceDelta: number;
  items: StoreItem[];
  previousBalance: number;
}): EconomyAction {
  const availableItems = getAffordableStoreItems(params.items);
  return {
    wallet: null,
    available_items: availableItems,
    newly_affordable_items: availableItems.filter((item) => params.previousBalance < item.price),
    best_item: pickBestStoreItem(params.items),
    balance_delta: params.balanceDelta,
    completed_mission_slugs: [],
    near_miss_message: null,
  };
}
