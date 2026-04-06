"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  fetchScenarioMarketplace,
  fetchScenarioShowcase,
  forkScenarioMarketplaceBlueprint,
  likeScenarioMarketplaceBlueprint,
} from "@/lib/client-api";
import type { ScenarioBlueprintRead, ScenarioShowcaseRead } from "@/lib/types";

export default function ScenarioMarketplacePage() {
  const [items, setItems] = useState<ScenarioBlueprintRead[]>([]);
  const [showcase, setShowcase] = useState<ScenarioShowcaseRead[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function reload() {
    const [marketplaceRows, showcaseRows] = await Promise.all([
      fetchScenarioMarketplace(24).catch(() => []),
      fetchScenarioShowcase(12).catch(() => []),
    ]);
    setItems(marketplaceRows);
    setShowcase(showcaseRows);
  }

  useEffect(() => {
    void reload();
  }, []);

  async function handleFork(id: string) {
    try {
      const result = await forkScenarioMarketplaceBlueprint(id);
      setMessage(
        result.token_spent > 0
          ? `Forked. Spent ${result.token_spent} tokens.`
          : "Forked blueprint.",
      );
      await reload();
    } catch {
      setMessage("Could not fork this blueprint.");
    }
  }

  async function handleLike(id: string) {
    try {
      await likeScenarioMarketplaceBlueprint(id);
      setMessage("Blueprint liked.");
      await reload();
    } catch {
      setMessage("Could not like this blueprint.");
    }
  }

  return (
    <div className="pv-page mx-auto max-w-6xl">
      <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">Scenario Marketplace</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">
          Discover creator scenarios and fork instantly.
        </h1>
        <p className="mt-3 pv-lead max-w-3xl">
          Public blueprints, creator rewards, and shareable outputs in one workflow.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/studio" className="pv-button-primary !w-auto">
            Open Studio
          </Link>
          <Link href="/" className="pv-button-secondary !w-auto">
            Back to Home
          </Link>
        </div>
        {message ? <p className="mt-4 text-sm font-semibold text-emerald-700">{message}</p> : null}
      </section>

      <section className="pv-panel px-5 py-5 sm:px-7 sm:py-6">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Blueprints</h2>
          <p className="mt-2 text-sm text-zinc-600">Fork proven templates and adapt them for your flow.</p>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <article key={item.id} className="pv-card flex h-full flex-col p-4">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{item.summary ?? "No summary"}</p>
              <p className="mt-3 text-xs text-zinc-500">
                forks: {item.fork_count} | likes: {item.like_count}
              </p>
              <div className="mt-auto flex flex-wrap gap-2 pt-4">
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleFork(item.id)}>
                  Fork
                </button>
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleLike(item.id)}>
                  Like
                </button>
              </div>
            </article>
          ))}
          {!items.length ? (
            <div className="pv-empty-state md:col-span-2 xl:col-span-3">
              <p className="text-sm text-zinc-600">No published blueprints yet.</p>
            </div>
          ) : null}
        </div>
      </section>

      <section className="pv-panel px-5 py-5 sm:px-7 sm:py-6">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Showcase Outputs</h2>
          <p className="mt-2 text-sm text-zinc-600">Examples from top forks that gained traction.</p>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {showcase.map((item) => (
            <article key={item.share_id} className="pv-card p-4">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{item.excerpt}</p>
              <pre className="mt-2 max-h-[6rem] overflow-auto rounded-[0.7rem] border border-zinc-200 bg-white p-2 text-[11px] leading-relaxed text-zinc-700 whitespace-pre-wrap">
                {item.output_preview}
              </pre>
            </article>
          ))}
          {!showcase.length ? (
            <div className="pv-empty-state md:col-span-2 xl:col-span-3">
              <p className="text-sm text-zinc-600">Showcase is empty.</p>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
