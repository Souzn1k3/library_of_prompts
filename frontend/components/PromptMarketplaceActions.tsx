"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import { buyPromptWithLumens, createPromptCheckoutSession } from "@/lib/client-api";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { languageToIntlLocale } from "@/lib/i18n";
import type { PromptAccess, PromptPrice } from "@/lib/types";

type Props = {
  promptId: string;
  promptSlug: string;
  price: PromptPrice | null | undefined;
  access: PromptAccess | null | undefined;
  bodyLocked: boolean;
};

function formatNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

export function PromptMarketplaceActions({ promptId, promptSlug, price, access, bodyLocked }: Props) {
  const router = useRouter();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const [pending, setPending] = useState<"lumens" | "checkout" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientTokenRef = useRef<string>(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  );

  if (!price) {
    return null;
  }

  async function onBuyWithLumens() {
    setError(null);
    setPending("lumens");
    try {
      await buyPromptWithLumens(promptId, clientTokenRef.current);
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("prompt.marketplace.errorLumens"));
    } finally {
      setPending(null);
    }
  }

  async function onCheckout() {
    setError(null);
    setPending("checkout");
    try {
      const currentUrl = typeof window !== "undefined" ? window.location.href : `/prompt/${promptSlug}`;
      const cancelUrl = typeof window !== "undefined" ? window.location.href : `/prompt/${promptSlug}`;
      const session = await createPromptCheckoutSession(promptId, clientTokenRef.current, {
        success_url: currentUrl,
        cancel_url: cancelUrl,
      });
      window.location.href = session.url;
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("prompt.marketplace.errorCheckout"));
      setPending(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="rounded-[1rem] border border-[var(--pv-border)] bg-white/80 p-4 text-sm text-zinc-700">
        <p className="font-medium text-zinc-950">
          {bodyLocked ? t("prompt.marketplace.bodyLocked") : t("prompt.marketplace.unlockedLibrary")}
        </p>
        <p className="mt-2">
          {bodyLocked
            ? access?.catalog_action === "signin"
              ? t("prompt.marketplace.signinPrompt")
              : access?.monthly_plan_unlocks
                ? t("prompt.marketplace.unlocksRemaining", {
                    remaining: access.remaining_plan_unlocks ?? 0,
                    total: access.monthly_plan_unlocks,
                  })
                : t("prompt.marketplace.permanentAccess")
            : access?.source === "subscription_limit"
              ? t("prompt.marketplace.openedByPlan")
              : access?.source === "direct_lumens"
                ? t("prompt.marketplace.purchasedLumens")
                : access?.source === "direct_money"
                  ? t("prompt.marketplace.purchasedCheckout")
                  : t("prompt.marketplace.permanentGranted")}
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-zinc-500">
          <span className="pv-chip">{formatNumber(price.price_rub, locale)} RUB</span>
          <span className="pv-chip">{formatNumber(price.price_lumens, locale)} {TOKEN_SHORT_CODE}</span>
          <span className="pv-chip">{t("prompt.marketplace.platformFee", { percent: price.commission_percent })}</span>
        </div>
      </div>

      {bodyLocked ? (
        access?.catalog_action === "signin" ? (
          <div className="flex flex-wrap gap-3">
            <Link href="/login" className="pv-button-primary">
              {t("prompt.marketplace.signin")}
            </Link>
            <Link href="/signup" className="pv-button-secondary">
              {t("prompt.marketplace.createAccount")}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={() => void onBuyWithLumens()}
              disabled={pending !== null}
              className="pv-button-primary disabled:opacity-60"
            >
              {pending === "lumens"
                ? t("prompt.marketplace.unlocking")
                : t("prompt.marketplace.buyWithLumens", { count: formatNumber(price.price_lumens, locale) })}
            </button>
            <button
              type="button"
              onClick={() => void onCheckout()}
              disabled={pending !== null}
              className="pv-button-secondary disabled:opacity-60"
            >
              {pending === "checkout"
                ? t("prompt.marketplace.openingCheckout")
                : t("prompt.marketplace.buyForRub", { count: formatNumber(price.price_rub, locale) })}
            </button>
          </div>
        )
      ) : null}

      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
