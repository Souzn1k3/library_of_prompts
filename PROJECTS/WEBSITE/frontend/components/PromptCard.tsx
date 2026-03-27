import Link from "next/link";

import { ContributorBadge } from "@/components/ContributorBadge";
import { T } from "@/components/i18n/T";
import { getDifficultyTranslationKey, getTechniqueTranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export function PromptCard({ prompt }: { prompt: PromptListItem }) {
  return (
    <Link
      href={`/prompt/${encodeURIComponent(prompt.slug)}`}
      className="group block rounded-lg border border-zinc-200 bg-white p-5 shadow-card transition hover:border-zinc-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-base font-semibold tracking-tight text-zinc-900 group-hover:underline">
          {prompt.title}
        </h2>
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-1">
          {prompt.is_premium ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900">
              <T k="prompt.premium" />
            </span>
          ) : null}
          {prompt.difficulty ? (
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-900">
              <T k={getDifficultyTranslationKey(prompt.difficulty)} />
            </span>
          ) : null}
          <ContributorBadge tier={prompt.contributor_tier} compact />
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
            <T k={getTechniqueTranslationKey(prompt.technique)} />
          </span>
        </div>
      </div>
      {prompt.summary ? (
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-zinc-600">
          {prompt.summary}
        </p>
      ) : (
        <p className="mt-2 text-sm text-zinc-400">
          <T k="prompt.noSummary" />
        </p>
      )}
      {prompt.recommendation_reason_key ? (
        <div className="mt-3 inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-medium text-amber-900">
          <T k={prompt.recommendation_reason_key} />
        </div>
      ) : null}
      <div className="mt-3 flex items-center gap-3 text-xs text-zinc-500">
        <span>
          <T k="prompt.savedLabel" />: {prompt.save_count ?? 0}
        </span>
        <span>
          <T k="prompt.copiedLabel" />: {prompt.copy_count ?? 0}
        </span>
        {prompt.contributor_reputation_score != null ? (
          <span>
            <T k="prompt.creatorScoreLabel" />: {prompt.contributor_reputation_score}
          </span>
        ) : null}
      </div>
      {prompt.contributor_slug ? (
        <div className="mt-2 text-xs text-zinc-500">
          <T k="prompt.byContributor" />{" "}
          <span className="font-medium text-zinc-700">@{prompt.contributor_slug}</span>
        </div>
      ) : null}
      {prompt.quality_score != null ? (
        <div className="mt-1 text-xs text-zinc-500">
          <T k="prompt.qualityLabel" />: {prompt.quality_score}
        </div>
      ) : null}
    </Link>
  );
}
