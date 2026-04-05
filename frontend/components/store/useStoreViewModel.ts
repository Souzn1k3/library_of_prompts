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
  STORE_SECTION_ORDER,
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

  const sections = useMemo(
    () =>
      STORE_SECTION_ORDER.map((kind) => ({
        kind,
        items: items.filter((item) => item.kind === kind),
      })).filter((section) => section.items.length > 0),
    [items],
  );

  return {
    affordableItems,
    nearMissItems,
    bestItem,
    bestItemTitle,
    successPurchaseItemTitle,
    successRewardCopy,
    successDiscountCode,
    sections,
  };
}
