"use client";

import { useMemo } from "react";

import {
  localizedStarterReward,
  localizedStoreItemTitle,
  textOrNull,
  type TranslateFn,
} from "@/components/store/presentation";
import {
  STORE_NEAR_MISS_ITEMS_LIMIT,
} from "@/lib/constants/economy-ui";
import {
  getAffordableStoreItems,
  getNearMissStoreItems,
  pickBestStoreItem,
} from "@/lib/economy";
import type { PurchaseResult, StoreItem } from "@/lib/types";

type UseStoreViewModelArgs = {
  items: StoreItem[];
  success: PurchaseResult | null;
  t: TranslateFn;
};

export function useStoreViewModel({ items, success, t }: UseStoreViewModelArgs) {
  const affordableItems = useMemo(() => getAffordableStoreItems(items), [items]);
  const nearMissItems = useMemo(
    () => getNearMissStoreItems(items, STORE_NEAR_MISS_ITEMS_LIMIT),
    [items],
  );
  const bestItem = useMemo(() => pickBestStoreItem(items), [items]);
  const bestItemTitle = useMemo(
    () => (bestItem ? localizedStoreItemTitle(bestItem, t) : null),
    [bestItem, t],
  );
  const successPurchaseItemTitle = useMemo(
    () => (success ? localizedStoreItemTitle(success.purchase.item, t) : null),
    [success, t],
  );
  const successRewardCopy = useMemo(
    () =>
      success
        ? localizedStarterReward({
            slug: success.purchase.item.slug,
            t,
            fallbackTitle: textOrNull(success.purchase.metadata?.reward_title),
            fallbackBody: textOrNull(success.purchase.metadata?.reward_body),
          })
        : null,
    [success, t],
  );
  const successDiscountCode = useMemo(
    () =>
      success && typeof success.purchase.metadata?.discount_code === "string"
        ? success.purchase.metadata.discount_code
        : null,
    [success],
  );

  const feedItems = useMemo(() => {
    function rank(item: StoreItem): number {
      const soldOut = item.availability !== null && item.availability <= 0;
      if (item.owned) return 4;
      if (soldOut) return 5;
      if (item.is_affordable) return 1;
      if (item.near_miss_delta <= STORE_NEAR_MISS_ITEMS_LIMIT * 5) return 2;
      return 3;
    }

    return [...items].sort((left, right) => {
      const rankDiff = rank(left) - rank(right);
      if (rankDiff !== 0) return rankDiff;

      if (left.is_affordable && right.is_affordable) {
        return left.price - right.price;
      }

      if (!left.is_affordable && !right.is_affordable) {
        return left.remaining_lumens - right.remaining_lumens;
      }

      return left.price - right.price;
    });
  }, [items]);

  return {
    affordableItems,
    nearMissItems,
    bestItem,
    bestItemTitle,
    successPurchaseItemTitle,
    successRewardCopy,
    successDiscountCode,
    feedItems,
  };
}
