"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getContributorTierTranslationKey } from "@/lib/i18n";
import type { ContributorTier } from "@/lib/types";

function tierClasses(tier: ContributorTier | null | undefined): string {
  if (tier === "top") return "border border-[var(--pv-border-strong)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]";
  if (tier === "verified") return "border border-[rgba(38,122,94,0.3)] bg-[#edf8f3] text-[#1f5e49]";
  if (tier === "new") return "border border-zinc-200 bg-zinc-50 text-zinc-700";
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
