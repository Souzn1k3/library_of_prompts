"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getContributorTierTranslationKey } from "@/lib/i18n";
import type { ContributorTier } from "@/lib/types";

function tierClasses(tier: ContributorTier | null | undefined): string {
  if (tier === "top") return "bg-amber-100 text-amber-900";
  if (tier === "verified") return "bg-emerald-100 text-emerald-900";
  if (tier === "new") return "bg-blue-100 text-blue-900";
  return "bg-zinc-100 text-zinc-700";
}

export function ContributorBadge({
  tier,
  compact = false,
}: {
  tier: ContributorTier | null | undefined;
  compact?: boolean;
}) {
  const { t } = useI18n();
  if (!tier) return null;
  const fullLabel = t(getContributorTierTranslationKey(tier));
  const compactLabel = fullLabel
    .replace(/\sContributor$/i, "")
    .replace(/\sавтор$/i, "")
    .replace(/\sАвтор$/i, "")
    .trim();
  return (
    <span
      className={`rounded-full px-2 py-0.5 ${compact ? "text-[11px]" : "text-xs"} ${tierClasses(tier ?? null)}`}
      title={fullLabel}
    >
      {compact ? compactLabel : fullLabel}
    </span>
  );
}
