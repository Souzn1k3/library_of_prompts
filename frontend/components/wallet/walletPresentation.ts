import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatDateTime, formatNumber, humanizeSnakeCase } from "@/lib/formatters";
import type { TranslationKey } from "@/lib/i18n";
import type { StoreItem, WalletBenefit, WalletRead } from "@/lib/types";

export type WalletTranslate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

function readBenefitString(benefit: WalletBenefit, key: string): string | null {
  const value = benefit.metadata?.[key];
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function readBenefitNumber(benefit: WalletBenefit, key: string): number | null {
  const value = benefit.metadata?.[key];
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function formatSignedAmount(amount: number): string {
  const sign = amount > 0 ? "+" : "";
  return `${sign}${amount}`;
}

export function reasonLabel(reason: string, t: WalletTranslate): string {
  const key = `wallet.transaction.reason.${reason}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(reason) : translated;
}

export function benefitLabel(benefit: WalletBenefit, t: WalletTranslate, locale: string): string {
  if (benefit.kind === "subscription_discount" || benefit.kind === "starter") {
    const code = typeof benefit.metadata?.code === "string" ? benefit.metadata.code : null;
    const percent = benefit.metadata?.discount_percent;
    if (code) {
      if (typeof percent === "number") {
        return `${formatNumber(percent, locale)}% · ${code}`;
      }
      return code;
    }
    return typeof benefit.metadata?.item_title === "string"
      ? String(benefit.metadata.item_title)
      : t("store.kind.starter");
  }
  if (benefit.kind === "premium_access") {
    return t("store.kind.premium_pass");
  }
  if (benefit.kind === "premium_prompt_unlock") {
    return typeof benefit.metadata?.prompt_title === "string"
      ? String(benefit.metadata.prompt_title)
      : t("store.kind.premium_prompt_unlock");
  }
  if (benefit.kind === "prompt_bundle") {
    return typeof benefit.metadata?.item_title === "string"
      ? String(benefit.metadata.item_title)
      : t("store.kind.prompt_bundle");
  }
  if (benefit.kind === "boost") {
    const itemSlug = readBenefitString(benefit, "item_slug");
    if (itemSlug) {
      const key = `store.item.${itemSlug}.title` as TranslationKey;
      const translated = t(key);
      if (translated !== key) {
        return translated;
      }
    }

    const itemTitle = readBenefitString(benefit, "item_title");
    if (itemTitle) {
      return itemTitle;
    }

    const boostPct = readBenefitNumber(benefit, "boost_pct");
    if (boostPct !== null) {
      return t("wallet.boostTitleWithPercent", { percent: formatNumber(boostPct, locale) });
    }

    return t("store.kind.boost");
  }
  return humanizeSnakeCase(benefit.kind);
}

export function benefitKindLabel(kind: string, t: WalletTranslate): string {
  if (kind === "premium_access") {
    return t("store.kind.premium_pass");
  }
  if (kind === "boost") {
    return t("store.kind.boost");
  }
  const key = `store.kind.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(kind) : translated;
}

export function benefitMetaLines(
  benefit: WalletBenefit,
  t: WalletTranslate,
  locale: string,
): string[] {
  if (benefit.kind === "boost") {
    const boostPct = readBenefitNumber(benefit, "boost_pct");
    const missionsLeft = readBenefitNumber(benefit, "boost_missions_left");
    const missionsTotal =
      readBenefitNumber(benefit, "boost_missions_total") ?? readBenefitNumber(benefit, "boost_missions");
    const lines: string[] = [];

    if (missionsLeft !== null && missionsTotal !== null && missionsTotal > 0) {
      lines.push(
        t("wallet.boostMissionsLeft", {
          left: formatNumber(Math.max(0, missionsLeft), locale),
          total: formatNumber(Math.max(0, missionsTotal), locale),
          percent: boostPct !== null ? formatNumber(boostPct, locale) : 0,
        }),
      );
    } else if (boostPct !== null) {
      lines.push(
        t("wallet.boostPercentOnly", {
          percent: formatNumber(boostPct, locale),
        }),
      );
    }

    if (benefit.expires_at) {
      lines.push(
        t("wallet.boostExpiresAt", {
          date: formatDateTime(benefit.expires_at, locale),
        }),
      );
    }
    return lines;
  }

  if (benefit.expires_at) {
    return [`${t("wallet.premiumUntil")}: ${formatDateTime(benefit.expires_at, locale)}`];
  }
  return [];
}

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

export function formatBalanceDelta(amount: number): string {
  return `${formatSignedAmount(amount)} ${TOKEN_SHORT_CODE}`;
}
