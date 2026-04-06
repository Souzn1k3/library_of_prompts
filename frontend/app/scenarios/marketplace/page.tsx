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
    <div className="mx-auto max-w-6xl space-y-5">
      <section className="pv-panel p-5">
        <p className="pv-kicker">Scenario Marketplace</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-zinc-950">
          Discover creator scenarios and fork instantly.
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          Public blueprints, creator rewards, and shareable outputs are part of the core growth loop.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link href="/studio" className="pv-button-primary !w-auto">
            Open Studio
          </Link>
          <Link href="/" className="pv-button-secondary !w-auto">
            Back to Home
          </Link>
        </div>
        {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
      </section>

      <section className="pv-panel p-5">
        <h2 className="text-lg font-semibold text-zinc-950">Blueprints</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {items.map((item) => (
            <article key={item.id} className="rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{item.summary ?? "No summary"}</p>
              <p className="mt-1 text-xs text-zinc-500">
                forks: {item.fork_count} | likes: {item.like_count}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleFork(item.id)}>
                  Fork
                </button>
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleLike(item.id)}>
                  Like
                </button>
              </div>
            </article>
          ))}
          {!items.length ? <p className="text-sm text-zinc-600">No published blueprints yet.</p> : null}
        </div>
      </section>

      <section className="pv-panel p-5">
        <h2 className="text-lg font-semibold text-zinc-950">Showcase Outputs</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {showcase.map((item) => (
            <article key={item.share_id} className="rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{item.excerpt}</p>
              <pre className="mt-2 max-h-[6rem] overflow-auto rounded-[0.7rem] border border-zinc-200 bg-white p-2 text-[11px] leading-relaxed text-zinc-700 whitespace-pre-wrap">
                {item.output_preview}
              </pre>
            </article>
          ))}
          {!showcase.length ? <p className="text-sm text-zinc-600">Showcase is empty.</p> : null}
        </div>
      </section>
    </div>
  );
}
