import Link from "next/link";

import type { PromptListItem } from "@/lib/types";

function techniqueLabel(t: PromptListItem["technique"]): string {
  switch (t) {
    case "zero_shot":
      return "Zero-shot";
    case "few_shot":
      return "Few-shot";
    case "chain_of_thought":
      return "Chain-of-thought";
    default:
      return "Other";
  }
}

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
              Premium
            </span>
          ) : null}
          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-700">
            {techniqueLabel(prompt.technique)}
          </span>
        </div>
      </div>
      {prompt.summary ? (
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-zinc-600">
          {prompt.summary}
        </p>
      ) : (
        <p className="mt-2 text-sm text-zinc-400">No summary</p>
      )}
    </Link>
  );
}
