"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getContributorTierTranslationKey } from "@/lib/i18n";
import type { ContributorTier } from "@/lib/types";

function tierClasses(tier: ContributorTier | null | undefined): string {
  if (tier === "top") return "border border-[#e9d8af] bg-[#f8f2e5] text-[#8a6119]";
  if (tier === "verified") return "border border-[#cae5da] bg-[#edf8f2] text-[#1b6a53]";
  if (tier === "new") return "border border-[#d8e4ff] bg-[#eff4ff] text-[#3d568d]";
  return "border border-zinc-200 bg-zinc-100 text-zinc-700";
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
