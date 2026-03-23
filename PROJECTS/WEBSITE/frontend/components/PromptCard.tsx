import Link from "next/link";

import { T } from "@/components/i18n/T";
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
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
            {prompt.technique === "zero_shot" ? (
              <T k="catalogFilters.zeroShot" />
            ) : prompt.technique === "few_shot" ? (
              <T k="catalogFilters.fewShot" />
            ) : prompt.technique === "chain_of_thought" ? (
              <T k="catalogFilters.chainOfThought" />
            ) : (
              <T k="catalogFilters.other" />
            )}
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
    </Link>
  );
}
