import Link from "next/link";

import { T } from "@/components/i18n/T";
import { getDifficultyTranslationKey, getTechniqueTranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export function PromptCard({ prompt }: { prompt: PromptListItem }) {
  return (
    <Link href={`/prompt/${encodeURIComponent(prompt.slug)}`} className="pv-card group block p-5">
      <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
        <span className="font-medium text-zinc-700">
          <T k={getTechniqueTranslationKey(prompt.technique)} />
        </span>
        {prompt.difficulty ? (
          <span>
            · <T k={getDifficultyTranslationKey(prompt.difficulty)} />
          </span>
        ) : null}
        {prompt.is_premium ? (
          <span className="text-amber-700">
            · <T k="prompt.premium" />
          </span>
        ) : null}
      </div>

      <div className="mt-3 space-y-2">
        <h2 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950 transition group-hover:text-[var(--pv-brand)]">
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

      <div className="mt-4 flex items-center justify-between gap-3 border-t border-[var(--pv-border)] pt-4">
        <p className="text-xs text-zinc-500">
          {prompt.recommendation_reason_key ? <T k={prompt.recommendation_reason_key} /> : <T k="prompt.savedLabel" />}
        </p>
        <span className="text-sm font-medium text-[var(--pv-brand)]">
          <T k="prompt.openPrompt" />
        </span>
      </div>
    </Link>
  );
}
