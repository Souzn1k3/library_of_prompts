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

  const initialRating = purchase.review?.rating ?? 5;
  const initialText = purchase.review?.text ?? "";
  const normalizedText = text.trim();
  const isDirty = rating !== initialRating || normalizedText !== initialText.trim();
  const reviewBlockedReason =
    purchase.status === "refunded"
      ? t("profile.refundedPurchasesNoReviews")
      : purchase.status === "completed"
        ? t("profile.reviewAvailableWhenAttached")
        : t("profile.reviewAvailableForCompleted");

  function resetDraft() {
    setRating(initialRating);
    setText(initialText);
    setError(null);
    setSavedMessage(null);
  }

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
    <div className="rounded-[1rem] border border-zinc-200 bg-white/75 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href={appRoute.promptBySlug(purchase.prompt_slug)}
            className="inline-block max-w-full truncate text-lg font-semibold text-zinc-900 underline"
          >
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
        </div>

        <Link href={appRoute.promptBySlug(purchase.prompt_slug)} className="pv-button-secondary !w-auto">
          {t("profile.openPromptFromPurchase")}
        </Link>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="rounded-[0.95rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] p-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
            {t("profile.purchaseFlowStepAccess")}
          </p>
          <p className="mt-2 text-sm font-semibold text-zinc-900">
            {purchase.can_review ? t("profile.purchaseAccessReadyTitle") : t("profile.purchaseAccessLockedTitle")}
          </p>
          <p className="mt-1 text-sm text-zinc-600">
            {purchase.can_review ? t("profile.purchaseAccessReadyBody") : reviewBlockedReason}
          </p>
          {purchase.review ? (
            <>
              <p className="mt-3 text-xs text-zinc-500">
                {t("profile.lastReviewUpdate", { date: formatDate(purchase.review.updated_at, locale) })}
              </p>
              <p className="mt-1 text-xs text-zinc-500">
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

        <div className="rounded-[0.95rem] border border-[var(--pv-border)] bg-white p-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
            {t("profile.purchaseFlowStepRating")}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setRating(value)}
                disabled={!purchase.can_review}
                className={`pv-review-rating ${value <= rating ? "pv-review-rating-active" : ""} disabled:opacity-60`}
              >
                <span className="pv-review-rating-star" aria-hidden="true">
                  ★
                </span>
                <span>{value}</span>
              </button>
            ))}
          </div>
          <p className="mt-2 text-sm text-zinc-600">{t("profile.purchaseRatingSelected", { rating })}</p>
        </div>
      </div>

      {purchase.can_review ? (
        <div className="mt-3 rounded-[0.95rem] border border-[var(--pv-border)] bg-white p-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-zinc-500">
              {t("profile.purchaseFlowStepComment")}
            </p>
            {isDirty ? (
              <button type="button" onClick={resetDraft} className="pv-button-ghost !w-auto text-xs">
                {t("profile.reviewResetDraft")}
              </button>
            ) : null}
          </div>

          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={4}
            className="pv-textarea mt-2"
            placeholder={t("profile.reviewPlaceholder")}
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => void submit()}
              disabled={pending || !isDirty}
              className="pv-button-primary disabled:opacity-60"
            >
              {pending ? t("profile.saving") : purchase.review ? t("profile.updateReview") : t("profile.saveReview")}
            </button>
            {!isDirty ? <span className="text-sm text-zinc-500">{t("profile.reviewNoChanges")}</span> : null}
            {savedMessage ? <span className="text-sm text-emerald-700">{savedMessage}</span> : null}
            {error ? <span className="text-sm text-red-700">{error}</span> : null}
          </div>
          {purchase.review?.moderation_status === "pending" ? (
            <p className="mt-3 text-sm text-amber-700">{t("profile.reviewPendingModeration")}</p>
          ) : null}
          {purchase.review?.moderation_status === "hidden" ? (
            <p className="mt-3 text-sm text-zinc-600">{t("profile.reviewHiddenNotice")}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
