"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  localizedStarterReward,
  localizedStoreItemDescription,
  localizedStoreItemTitle,
  textOrNull,
} from "@/components/store/presentation";
import { LmnMark } from "@/components/ui/LmnMark";
import { STORE_KIND_TONE } from "@/lib/constants/economy-ui";
import { APP_ROUTES } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import type { StoreItem } from "@/lib/types";

type StoreItemCardProps = {
  item: StoreItem;
  purchasing: string | null;
  onPurchase: (item: StoreItem) => Promise<void>;
  locale: string;
};

export function StoreItemCard({
  item,
  purchasing,
  onPurchase,
  locale,
}: StoreItemCardProps) {
  const { t } = useI18n();
  const soldOut = item.availability !== null && item.availability <= 0;
  const disabled = purchasing === item.slug || soldOut || item.owned || !item.is_affordable;
  const progressPct = Math.max(item.progress_ratio > 0 ? 8 : 0, Math.min(100, Math.round(item.progress_ratio * 100)));
  const tone = STORE_KIND_TONE[item.kind];
  const title = localizedStoreItemTitle(item, t);
  const description = localizedStoreItemDescription(item, t);
  const currencySymbol = TOKEN_SHORT_CODE;
  const starterRewardCopy = localizedStarterReward({
    slug: item.slug,
    t,
    fallbackTitle: textOrNull(item.metadata?.reward_title),
    fallbackBody: textOrNull(item.metadata?.reward_body),
  });

  return (
    <article className="pv-card flex flex-col justify-between gap-5 p-5">
      <div className="relative flex h-full flex-col gap-5">
        <div className="space-y-2">
          <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">{title}</h3>
          {description ? <p className="text-sm leading-relaxed text-zinc-600">{description}</p> : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {item.owned ? <span className="pv-badge-success">{t("store.owned")}</span> : null}
          {soldOut ? <span className="pv-badge-danger">{t("store.soldOut")}</span> : null}
          {!soldOut && !item.owned && !item.is_affordable ? (
            <span className="pv-badge-warning">{t("store.needMore", { count: formatNumber(item.near_miss_delta, locale) })}</span>
          ) : null}
        </div>

        {!item.owned && !soldOut ? (
          <div className="pv-card-muted p-3">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-zinc-900">
                {item.is_affordable
                  ? t("store.readyToBuy")
                  : t("store.needMore", { count: formatNumber(item.near_miss_delta, locale) })}
              </span>
              <span className="text-zinc-500">{progressPct}%</span>
            </div>
            <div className="mt-3 pv-progress">
              <div className="pv-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        ) : null}

        {item.kind === "starter" && (starterRewardCopy.title || starterRewardCopy.body) ? (
          <div className="pv-card-muted p-3 text-sm text-zinc-600">
            {starterRewardCopy.title ? <span className="font-medium text-zinc-900">{starterRewardCopy.title}</span> : null}
            {starterRewardCopy.body ? <p className="mt-1">{starterRewardCopy.body}</p> : null}
          </div>
        ) : null}

        {item.owned ? (
          <button
            type="button"
            disabled
            className={`pv-button-primary mt-auto disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
          >
            {t("store.owned")}
          </button>
        ) : soldOut ? (
          <button
            type="button"
            disabled
            className={`pv-button-primary mt-auto disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
          >
            {t("store.soldOut")}
          </button>
        ) : item.is_affordable ? (
          <button
            type="button"
            onClick={() => void onPurchase(item)}
            disabled={disabled}
            className={`pv-button-primary mt-auto gap-2 disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
          >
            {purchasing === item.slug ? (
              t("missions.loading")
            ) : (
              <>
                <span>{t("store.purchase")}</span>
                <span className="inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-white/15 px-2.5 py-1 text-[11px] font-semibold tracking-[0.06em] text-white/95">
                  <LmnMark size={14} label={currencySymbol} tone="balance" />
                  <span>{formatNumber(item.price, locale)}</span>
                  <span className="text-white/85">{currencySymbol}</span>
                </span>
              </>
            )}
          </button>
        ) : (
          <Link href={APP_ROUTES.missions} className="pv-button-secondary mt-auto !w-auto justify-center">
            {t("economy.earnCta")}
          </Link>
        )}
      </div>
    </article>
  );
}
