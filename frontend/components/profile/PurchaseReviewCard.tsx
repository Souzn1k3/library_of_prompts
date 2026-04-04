"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  humanizePaymentMethod,
  humanizePurchaseStatus,
  humanizeReviewModerationReason,
  humanizeReviewModerationStatus,
  humanizeSettlementStatus,
} from "@/components/profile/presentation";
import { ApiRequestError } from "@/lib/api";
import { upsertPromptReview } from "@/lib/client-api";
import { appRoute } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDate, formatNumber } from "@/lib/formatters";
import type { PromptMarketplacePurchase } from "@/lib/types";

type PurchaseReviewCardProps = {
  locale: string;
  purchase: PromptMarketplacePurchase;
  onSubmitted: () => void;
};

export function PurchaseReviewCard({ locale, purchase, onSubmitted }: PurchaseReviewCardProps) {
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
                : `${formatNumber(purchase.price_lumens, locale)} ${TOKEN_SHORT_CODE}`}
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
