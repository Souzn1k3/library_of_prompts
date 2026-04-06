"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createScenarioMarketplaceComment,
  fetchScenarioMarketplace,
  fetchScenarioMarketplaceComments,
  forkScenarioMarketplaceBlueprint,
  likeScenarioMarketplaceBlueprint,
  rateScenarioMarketplaceBlueprint,
  remixScenarioMarketplaceBlueprint,
  saveScenarioMarketplaceBlueprint,
  trackScenarioMarketplaceUsage,
} from "@/lib/client-api";
import type {
  ScenarioBlueprintCommentRead,
  ScenarioBlueprintRead,
} from "@/lib/types";
import {
  ScenarioAppRuntime,
  scenarioPlatformActions,
  type ScenarioDefinition,
} from "@/features/scenario-engine";

type MarketplaceSection = "trending" | "new" | "top" | "best" | "personalized";

const SECTION_OPTIONS: Array<{ id: MarketplaceSection; label: string }> = [
  { id: "trending", label: "Trending" },
  { id: "new", label: "New" },
  { id: "top", label: "Top" },
  { id: "best", label: "Best" },
  { id: "personalized", label: "Personalized" },
];

function buildPreviewDefinition(item: ScenarioBlueprintRead): ScenarioDefinition {
  const raw = (item.logic_text ?? "").trim();
  if (raw.startsWith("{")) {
    try {
      return JSON.parse(raw) as ScenarioDefinition;
    } catch {
      // fallback below
    }
  }
  return {
    id: `market-preview-${item.slug}`,
    type: "tool",
    version: 3,
    title: item.title,
    description: item.summary ?? "Marketplace preview",
    layout: {
      panels: [
        {
          id: "hero",
          kind: "hero",
          renderer: "dom",
          kicker: "Preview",
          title: item.title,
          subtitle: item.summary ?? "Run this scenario and remix.",
        },
        {
          id: "text",
          kind: "section",
          renderer: "dom",
          title: "Blueprint logic",
          children: [
            {
              id: "logic",
              kind: "text",
              renderer: "dom",
              text: item.logic_text || "No logic preview available.",
            },
          ],
        },
      ],
    },
    inputs: { fields: [], interactions: [] },
    logic: { entryEvents: ["app/init"], steps: [] },
    output: { renderer: "dom", liveUpdates: true },
    state: {
      variables: [],
      persistence: { key: `marketplace-preview-${item.slug}`, local: true, server: false },
    },
    permissions: { defaultTier: "free", gates: [], usageLimits: [] },
    sandbox: { allowedActions: ["runtime.noop"] },
  };
}

export default function ScenarioMarketplacePage() {
  const [items, setItems] = useState<ScenarioBlueprintRead[]>([]);
  const [section, setSection] = useState<MarketplaceSection>("trending");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [message, setMessage] = useState<string | null>(null);
  const [activePreviewId, setActivePreviewId] = useState<string | null>(null);
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);
  const [comments, setComments] = useState<ScenarioBlueprintCommentRead[]>([]);
  const [newComment, setNewComment] = useState("");
  const [rating, setRating] = useState<number>(5);

  const reload = useCallback(async () => {
    const rows = await fetchScenarioMarketplace({
      limit: 24,
      section,
      search: search.trim() || undefined,
      category: category === "all" ? undefined : category,
    }).catch(() => []);
    setItems(rows);
  }, [category, search, section]);

  useEffect(() => {
    const handle = setTimeout(() => {
      void reload();
    }, 280);
    return () => clearTimeout(handle);
  }, [reload]);

  const activePreviewItem = useMemo(
    () => items.find((item) => item.id === activePreviewId) ?? null,
    [activePreviewId, items],
  );

  async function openComments(blueprintId: string) {
    const rows = await fetchScenarioMarketplaceComments(blueprintId, 30).catch(() => []);
    setActiveCommentId(blueprintId);
    setComments(rows);
  }

  async function handleComment(blueprintId: string) {
    if (!newComment.trim()) return;
    try {
      await createScenarioMarketplaceComment(blueprintId, { body: newComment.trim() });
      setNewComment("");
      await openComments(blueprintId);
      await reload();
      setMessage("Comment published.");
    } catch {
      setMessage("Could not publish comment.");
    }
  }

  return (
    <div className="pv-page mx-auto max-w-7xl">
      <section className="pv-hero px-6 py-7 sm:px-8 sm:py-8">
        <p className="pv-kicker">Scenario Marketplace</p>
        <h1 className="pv-title max-w-4xl text-zinc-950">User-generated scenario network</h1>
        <p className="mt-3 pv-lead max-w-3xl">
          Discover, run, save, comment, rate, fork, and remix scenarios. Every action feeds creator growth and discovery ranking.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/studio" className="pv-button-primary !w-auto">Open Studio</Link>
          <Link href="/" className="pv-button-secondary !w-auto">Back Home</Link>
        </div>
        {message ? <p className="mt-4 text-sm font-semibold text-emerald-700">{message}</p> : null}
      </section>

      <section className="pv-panel px-5 py-5 sm:px-7 sm:py-6">
        <div className="flex flex-wrap items-center gap-2">
          {SECTION_OPTIONS.map((entry) => (
            <button
              key={entry.id}
              type="button"
              className={section === entry.id ? "pv-button-primary !w-auto" : "pv-button-secondary !w-auto"}
              onClick={() => setSection(entry.id)}
            >
              {entry.label}
            </button>
          ))}
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-[1fr_220px]">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="pv-input"
            placeholder="Search scenarios, tags, creators"
          />
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="pv-input">
            <option value="all">all categories</option>
            <option value="growth">growth</option>
            <option value="utility">utility</option>
            <option value="learning">learning</option>
            <option value="productivity">productivity</option>
            <option value="entertainment">entertainment</option>
          </select>
        </div>
      </section>

      <section className="pv-panel mt-4 px-5 py-5 sm:px-7 sm:py-6">
        <div className="mt-1 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <article key={item.id} className="pv-card flex h-full flex-col p-4">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-xs text-zinc-600">{item.summary ?? "No summary"}</p>
              <p className="mt-2 text-[11px] text-zinc-500">
                by {item.author_display_name ?? item.owner_user_id.slice(0, 8)} · used {item.usage_count} · saves {item.save_count}
              </p>
              <p className="mt-1 text-[11px] text-zinc-500">
                rating {item.rating_average.toFixed(1)} ({item.rating_count}) · comments {item.comment_count}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void trackScenarioMarketplaceUsage(item.id, { event: "run" })}
                >
                  Run
                </button>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void saveScenarioMarketplaceBlueprint(item.id).then(() => reload())}
                >
                  Save
                </button>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void forkScenarioMarketplaceBlueprint(item.id).then(() => reload())}
                >
                  Fork
                </button>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void remixScenarioMarketplaceBlueprint(item.id).then(() => reload())}
                >
                  Remix
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void likeScenarioMarketplaceBlueprint(item.id).then(() => reload())}
                >
                  Like
                </button>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => setActivePreviewId(item.id)}
                >
                  Preview
                </button>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() => void openComments(item.id)}
                >
                  Comments
                </button>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <select value={rating} onChange={(event) => setRating(Number(event.target.value))} className="pv-input !w-auto">
                  <option value={5}>5</option><option value={4}>4</option><option value={3}>3</option><option value={2}>2</option><option value={1}>1</option>
                </select>
                <button
                  type="button"
                  className="pv-button-secondary !w-auto"
                  onClick={() =>
                    void rateScenarioMarketplaceBlueprint(item.id, { rating }).then(async () => {
                      await reload();
                      setMessage("Rating submitted.");
                    })
                  }
                >
                  Rate
                </button>
              </div>
            </article>
          ))}
        </div>
        {!items.length ? (
          <div className="pv-empty-state mt-4">
            <p className="text-sm text-zinc-600">No scenarios found for this segment.</p>
          </div>
        ) : null}
      </section>

      {activePreviewItem ? (
        <section className="pv-panel mt-4 px-5 py-5 sm:px-7 sm:py-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-xl font-semibold text-zinc-950">Interactive Preview: {activePreviewItem.title}</h2>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="pv-button-secondary !w-auto"
                onClick={() => void trackScenarioMarketplaceUsage(activePreviewItem.id, { event: "run" })}
              >
                Mark Run
              </button>
              <button
                type="button"
                className="pv-button-secondary !w-auto"
                onClick={() => void trackScenarioMarketplaceUsage(activePreviewItem.id, { event: "complete" })}
              >
                Mark Complete
              </button>
            </div>
          </div>
          <div className="mt-3 rounded-[0.9rem] border border-zinc-200 bg-zinc-50/70 p-3">
            <ScenarioAppRuntime
              definition={buildPreviewDefinition(activePreviewItem)}
              actions={scenarioPlatformActions}
            />
          </div>
        </section>
      ) : null}

      {activeCommentId ? (
        <section className="pv-panel mt-4 px-5 py-5 sm:px-7 sm:py-6">
          <h2 className="text-xl font-semibold text-zinc-950">Comments</h2>
          <div className="mt-3 space-y-2">
            {comments.map((item) => (
              <article key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-semibold text-zinc-900">
                  {item.author_display_name ?? "User"} · {new Date(item.created_at).toLocaleString()}
                </p>
                <p className="mt-1 text-sm text-zinc-700">{item.body}</p>
              </article>
            ))}
            {!comments.length ? <p className="text-sm text-zinc-600">No comments yet.</p> : null}
          </div>
          <textarea
            value={newComment}
            onChange={(event) => setNewComment(event.target.value)}
            className="pv-textarea mt-3 min-h-[86px]"
            placeholder="Leave feedback for creator..."
          />
          <button type="button" className="pv-button-primary mt-2 !w-auto" onClick={() => void handleComment(activeCommentId)}>
            Post Comment
          </button>
        </section>
      ) : null}
    </div>
  );
}
