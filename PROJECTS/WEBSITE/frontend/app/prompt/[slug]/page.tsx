import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { SavePromptButton } from "@/components/SavePromptButton";
import { ApiRequestError, fetchPromptBySlug } from "@/lib/api";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  try {
    const prompt = await fetchPromptBySlug(slug);
    return {
      title: prompt.title,
      description: prompt.summary ?? prompt.title,
    };
  } catch {
    return { title: "Prompt" };
  }
}

function techniqueLabel(t: string): string {
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

export default async function PromptPage(props: Props) {
  const { slug } = await props.params;

  try {
    const prompt = await fetchPromptBySlug(slug);

    return (
      <article className="space-y-8">
        <div className="space-y-3">
          <Link
            href="/catalog"
            className="text-xs font-medium text-zinc-500 transition hover:text-zinc-800"
          >
            ← Back to catalog
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
              {prompt.title}
            </h1>
            <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs text-zinc-700">
              {techniqueLabel(prompt.technique)}
            </span>
          </div>
          {prompt.summary ? (
            <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">{prompt.summary}</p>
          ) : null}
          {prompt.body_locked ? (
            <p className="max-w-2xl rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
              Preview only. Upgrade to Starter or higher (API: set <code className="font-mono">plan_tier</code>{" "}
              via admin) to load the full prompt body with a Bearer token.
            </p>
          ) : null}
        </div>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
            Prompt
          </h2>
          <pre className="mt-3 whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-mono text-sm leading-relaxed text-zinc-900">
            {prompt.body}
          </pre>
        </section>

        <SavePromptButton promptId={prompt.id} />
      </article>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-medium">Could not load prompt</p>
        <p className="mt-1 text-amber-800">
          {e instanceof ApiRequestError ? e.message : "Unexpected error."}
        </p>
        <Link href="/catalog" className="mt-3 inline-block text-amber-950 underline">
          Return to catalog
        </Link>
      </div>
    );
  }
}
