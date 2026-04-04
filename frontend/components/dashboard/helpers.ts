import type { TranslationKey } from "@/lib/i18n";
import type { OnboardingStarterPack, PromptListItem, PromptTechnique } from "@/lib/types";

export function billingStatusLabel(
  status: string | null | undefined,
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string,
): string | null {
  if (!status) {
    return null;
  }
  const key = `plans.billingStatus.${status}` as TranslationKey;
  const translated = t(key);
  return translated === key ? t("plans.billingStatus.unknown") : translated;
}

export function formatVisitLabel(
  value: string | null | undefined,
  locale: string,
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string,
): string {
  if (!value) {
    return t("dashboard.navLastVisitNever");
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return t("dashboard.navLastVisitNever");
  }

  const now = new Date();
  const nowDayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const parsedDayStart = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()).getTime();
  const dayDiff = Math.round((nowDayStart - parsedDayStart) / (24 * 60 * 60 * 1000));

  if (dayDiff === 0) {
    return t("dashboard.navLastVisitToday");
  }

  if (dayDiff === 1) {
    return t("dashboard.navLastVisitYesterday");
  }

  const formatted = new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(parsed);

  return t("dashboard.navLastVisitDate", { date: formatted });
}

export function normalizeStarterPrompt(prompt: OnboardingStarterPack["prompts"][number]): PromptListItem {
  return {
    id: prompt.id,
    slug: prompt.slug,
    title: prompt.title,
    summary: prompt.summary,
    technique: (prompt.technique as PromptTechnique) ?? "other",
    category_id: prompt.category_id,
    status: "published",
    moderation_state: "approved",
    author_id: null,
    created_at: new Date(0).toISOString(),
  };
}
