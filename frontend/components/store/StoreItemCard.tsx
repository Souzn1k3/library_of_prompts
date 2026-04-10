"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  localizedStarterReward,
  localizedStoreItemDescription,
  localizedStoreItemTitle,
  textOrNull,
} from "@/components/store/presentation";
import { StoreItemArtwork } from "@/components/store/StoreItemArtwork";
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
  const description = localizedStoreItemDescription(item, t) ?? "";
  const currencySymbol = TOKEN_SHORT_CODE;
  const starterRewardCopy = localizedStarterReward({
    slug: item.slug,
    t,
    fallbackTitle: textOrNull(item.metadata?.reward_title),
    fallbackBody: textOrNull(item.metadata?.reward_body),
  });
  const needMoreCopy = t("store.needMore", { count: formatNumber(item.near_miss_delta, locale) });
  const stateCopy = item.owned ? t("store.owned") : soldOut ? t("store.soldOut") : item.is_affordable ? t("store.readyToBuy") : needMoreCopy;

  return (
    <article className="pv-card pv-store-feed-card">
      <StoreItemArtwork item={item} title={title} />

      <div className="flex flex-1 flex-col gap-4 p-4 sm:p-5">
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-900">{title}</h3>
            <span className="pv-store-price-chip">
              <LmnMark size={14} label={currencySymbol} tone="balance" />
              <span>{formatNumber(item.price, locale)}</span>
              <span className="text-[11px] text-zinc-500">{currencySymbol}</span>
            </span>
          </div>
          <p className="text-sm leading-relaxed text-zinc-600 line-clamp-3">{description}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="pv-store-state-chip">{stateCopy}</span>
          {!soldOut && !item.owned && !item.is_affordable ? (
            <span className="pv-badge-warning">{needMoreCopy}</span>
          ) : null}
          {item.dynamic_offer ? (
            <span className="pv-chip">{t("store.personalized")}</span>
          ) : null}
          {item.is_limited_offer ? (
            <span className="pv-chip">{t("store.limitedOffer")}</span>
          ) : null}
        </div>

        {!item.owned && !soldOut ? (
          <div className="pv-store-progress-wrap">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-zinc-900">
                {item.is_affordable
                  ? t("store.readyToBuy")
                  : needMoreCopy}
              </span>
              <span className="text-zinc-500">{progressPct}%</span>
            </div>
            <div className="mt-2 pv-progress">
              <div className="pv-progress-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        ) : null}

        {item.kind === "starter" && (starterRewardCopy.title || starterRewardCopy.body) ? (
          <div className="pv-store-reward-note text-sm text-zinc-600">
            {starterRewardCopy.title ? <span className="font-medium text-zinc-900">{starterRewardCopy.title}</span> : null}
            {starterRewardCopy.body ? <p className="mt-1">{starterRewardCopy.body}</p> : null}
          </div>
        ) : null}

        <div className="mt-auto pt-1">
          {item.owned ? (
            <button
              type="button"
              disabled
              className={`inline-flex min-h-[2.9rem] w-full items-center justify-center rounded-full bg-[var(--pv-brand)] px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(37,92,255,0.3)] transition disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
            >
              {t("store.owned")}
            </button>
          ) : soldOut ? (
            <button
              type="button"
              disabled
              className={`inline-flex min-h-[2.9rem] w-full items-center justify-center rounded-full bg-[var(--pv-brand)] px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(37,92,255,0.3)] transition disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
            >
              {t("store.soldOut")}
            </button>
          ) : item.is_affordable ? (
            <button
              type="button"
              onClick={() => void onPurchase(item)}
              disabled={disabled}
              className={`inline-flex min-h-[2.9rem] w-full items-center justify-center gap-2 rounded-full bg-[var(--pv-brand)] px-4 py-3 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(37,92,255,0.3)] transition disabled:cursor-not-allowed disabled:opacity-75 ${tone.button}`}
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
            <Link href={APP_ROUTES.missions} className="pv-button-secondary !w-full justify-center">
              {t("economy.earnCta")}
            </Link>
          )}
        </div>
      </div>
    </article>
  );
}
