import Link from "next/link";

import { ContributorBadge } from "@/components/ContributorBadge";
import { T } from "@/components/i18n/T";
import { getDifficultyTranslationKey, getTechniqueTranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export function PromptCard({ prompt }: { prompt: PromptListItem }) {
  const tone = getTechniqueTone(prompt.technique);
  const ctaLabelKey = getPromptCtaLabelKey(prompt);
  const isPaid = Boolean(prompt.is_paid && prompt.price);

  return (
    <Link
      href={`/prompt/${encodeURIComponent(prompt.slug)}`}
      prefetch={false}
      className="pv-card pv-card-optimized group block p-5"
    >
      <div className={`pv-prompt-card-glow ${tone.glow}`} />

        <div className="relative flex h-full flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              <span className={`pv-badge ${tone.badge}`}>
                <T k={getTechniqueTranslationKey(prompt.technique)} />
              </span>
            {prompt.difficulty ? (
              <span className="pv-badge">
                <T k={getDifficultyTranslationKey(prompt.difficulty)} />
              </span>
            ) : null}
            {isPaid ? (
              <span className="pv-badge-warning">
                <T k="prompt.paid" />
              </span>
            ) : prompt.is_premium ? (
              <span className="pv-badge-warning">
                <T k="prompt.premium" />
              </span>
            ) : null}
          </div>
          <ContributorBadge tier={prompt.contributor_tier} compact />
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-[-0.04em] text-zinc-950 transition group-hover:text-[var(--pv-brand-strong)]">
            {prompt.title}
          </h2>
          {prompt.summary ? (
            <p className="line-clamp-3 text-sm leading-relaxed text-zinc-600">{prompt.summary}</p>
          ) : (
            <p className="text-sm text-zinc-400">
              <T k="prompt.noSummary" />
            </p>
          )}
        </div>

        {(prompt.save_count || prompt.copy_count || prompt.quality_score) ? (
          <div className="mt-auto flex flex-wrap gap-2 text-xs text-zinc-500">
            {prompt.save_count ? (
              <span className="pv-chip">
                <T k="prompt.metricSaves" params={{ count: prompt.save_count }} />
              </span>
            ) : null}
            {prompt.copy_count ? (
              <span className="pv-chip">
                <T k="prompt.metricCopies" params={{ count: prompt.copy_count }} />
              </span>
            ) : null}
            {prompt.quality_score ? (
              <span className="pv-chip">
                <T k="prompt.metricQuality" params={{ count: prompt.quality_score }} />
              </span>
            ) : null}
            {prompt.price ? (
              <span className="pv-chip">
                <T k="prompt.priceRub" params={{ count: prompt.price.price_rub }} />
              </span>
            ) : null}
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-3 border-t border-[var(--pv-border)] pt-4">
          <p className="text-xs text-zinc-500">
            {prompt.price
              ? prompt.access?.catalog_action === "buy"
                ? <T k="prompt.access.includedQuotaUsed" />
                : prompt.access?.catalog_action === "signin"
                  ? <T k="prompt.access.signInToUnlock" />
                  : prompt.access?.can_unlock_with_plan
                    ? <T k="prompt.access.unlocksLeft" params={{ count: prompt.access.remaining_plan_unlocks ?? 0 }} />
                    : <T k="prompt.access.permanentUnlock" />
              : prompt.recommendation_reason_key
                ? <T k={prompt.recommendation_reason_key} />
                : <T k="prompt.savedLabel" />}
          </p>
          <span className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
            <T k={ctaLabelKey} />
            <span aria-hidden="true">↗</span>
          </span>
        </div>
      </div>
    </Link>
  );
}

function getTechniqueTone(technique: PromptListItem["technique"]) {
  if (technique === "zero_shot") {
    return {
      badge: "border-[rgba(37,92,255,0.12)] bg-[rgba(37,92,255,0.06)] text-zinc-700",
      glow: "bg-[rgba(37,92,255,0.08)]",
    };
  }

  if (technique === "few_shot") {
    return {
      badge: "border-[rgba(17,184,164,0.14)] bg-[rgba(17,184,164,0.08)] text-zinc-700",
      glow: "bg-[rgba(17,184,164,0.09)]",
    };
  }

  if (technique === "chain_of_thought") {
    return {
      badge: "border-[rgba(99,102,241,0.12)] bg-[rgba(99,102,241,0.07)] text-zinc-700",
      glow: "bg-[rgba(99,102,241,0.08)]",
    };
  }

  return {
    badge: "",
    glow: "bg-[rgba(148,163,184,0.1)]",
  };
}

function getPromptCtaLabelKey(prompt: PromptListItem) {
  if (prompt.access?.catalog_action === "buy") {
    return "prompt.cta.buy";
  }
  if (prompt.access?.catalog_action === "signin") {
    return "prompt.cta.signin";
  }
  return "prompt.openPrompt";
}
