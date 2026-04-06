"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createScenarioBlueprint,
  fetchMyScenarioBlueprints,
  fetchScenarioBlueprintLineage,
  fetchScenarioBlueprintVersions,
  fetchScenarioMarketplace,
  forkScenarioMarketplaceBlueprint,
  likeScenarioMarketplaceBlueprint,
  patchScenarioBlueprint,
  publishScenarioBlueprint,
  remixScenarioMarketplaceBlueprint,
} from "@/lib/client-api";
import type {
  ScenarioBlueprintLineageRead,
  ScenarioBlueprintRead,
  ScenarioBlueprintVersionRead,
} from "@/lib/types";
import {
  ScenarioAppRuntime,
  scenarioPlatformActions,
  type ScenarioDefinition,
} from "@/features/scenario-engine";

import { ScenarioGeneratorLab } from "./ScenarioGeneratorLab";

type FormState = {
  slug: string;
  title: string;
  summary: string;
  category: "utility" | "learning" | "productivity" | "entertainment" | "growth";
  visibility: "private" | "public" | "premium";
  monetization: "free" | "pro_only" | "paid";
  tokenPrice: string;
  tags: string;
};

const INITIAL_FORM: FormState = {
  slug: "",
  title: "",
  summary: "",
  category: "growth",
  visibility: "private",
  monetization: "free",
  tokenPrice: "",
  tags: "",
};

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-|-$/g, "");
}

function buildPreviewDefinition(form: FormState, flowText: string): ScenarioDefinition {
  const id = slugify(form.slug || form.title || "studio-preview");
  return {
    id: `studio-${id}`,
    type: "tool",
    version: 3,
    title: form.title.trim() || "Scenario Preview",
    description: form.summary.trim() || "Runtime preview from Scenario Studio",
    layout: {
      panels: [
        {
          id: "hero",
          kind: "hero",
          renderer: "dom",
          kicker: "Scenario Builder",
          title: form.title.trim() || "Draft scenario",
          subtitle: `Visibility: ${form.visibility} · Monetization: ${form.monetization}`,
        },
        {
          id: "runtime",
          kind: "section",
          renderer: "dom",
          title: "Runtime preview",
          subtitle: "Run the draft as an interactive app.",
          children: [
            {
              id: "task-form",
              kind: "form",
              renderer: "dom",
              formId: "studio_form",
              fieldIds: ["task-input"],
              submitLabel: "Run",
              submitInteractionId: "task-submit",
            },
            {
              id: "output",
              kind: "text",
              renderer: "dom",
              text: "{{state.ui.output}}",
            },
          ],
        },
      ],
    },
    inputs: {
      fields: [
        {
          id: "task-input",
          formId: "studio_form",
          label: "Task",
          type: "textarea",
          bind: "ui.task",
          interactionId: "task-updated",
        },
      ],
      interactions: [
        { id: "task-updated", type: "input", source: "task-input", emits: "studio/task-updated" },
        { id: "task-submit", type: "submit", source: "studio_form", emits: "studio/run" },
      ],
    },
    logic: {
      entryEvents: ["app/init"],
      steps: [
        {
          id: "init",
          on: "app/init",
          actions: [
            { kind: "set", target: "ui.output", value: { template: `Ready.\n${flowText}` } },
            { kind: "set", target: "ui.flow", value: flowText },
          ],
        },
        {
          id: "task-sync",
          on: "studio/task-updated",
          actions: [{ kind: "set", target: "ui.last_task", value: { from: "event.payload.value", fallback: "" } }],
        },
        {
          id: "run",
          on: "studio/run",
          actions: [
            {
              kind: "set",
              target: "ui.output",
              value: {
                template: "Task: {{state.ui.last_task}}\n\nExecution:\n{{state.ui.flow}}",
              },
            },
          ],
        },
      ],
    },
    output: { renderer: "dom", liveUpdates: true },
    state: {
      variables: [
        { scope: "ui", key: "output", initial: "" },
        { scope: "ui", key: "last_task", initial: "" },
        { scope: "ui", key: "flow", initial: flowText },
      ],
      persistence: { key: `studio-preview-${id}`, local: true, server: false, autosaveMs: 500 },
      enableUndoRedo: true,
      enableReplay: true,
      resumeEvent: "app/init",
    },
    permissions: { defaultTier: "free", gates: [], usageLimits: [] },
    sandbox: { allowedActions: ["runtime.noop"], maxActionMs: 3000, maxEventsPerMinute: 200 },
  };
}

export function ScenarioStudioClient() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [flowText, setFlowText] = useState("1. Collect input\n2. Generate output\n3. Validate quality");
  const [dslText, setDslText] = useState("");
  const [dslError, setDslError] = useState<string | null>(null);
  const [previewDefinition, setPreviewDefinition] = useState<ScenarioDefinition | null>(null);

  const [mine, setMine] = useState<ScenarioBlueprintRead[]>([]);
  const [marketplace, setMarketplace] = useState<ScenarioBlueprintRead[]>([]);
  const [selectedBlueprintId, setSelectedBlueprintId] = useState<string | null>(null);
  const [versions, setVersions] = useState<ScenarioBlueprintVersionRead[]>([]);
  const [lineage, setLineage] = useState<ScenarioBlueprintLineageRead | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const canSave = useMemo(
    () => slugify(form.slug).length >= 3 && form.title.trim().length >= 3 && dslText.trim().length > 20,
    [dslText, form.slug, form.title],
  );

  const reload = useCallback(async () => {
    const [mineRows, marketRows] = await Promise.all([
      fetchMyScenarioBlueprints().catch(() => []),
      fetchScenarioMarketplace({ limit: 12, section: "trending" }).catch(() => []),
    ]);
    setMine(mineRows);
    setMarketplace(marketRows);
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  function syncDslFromBuilder() {
    const definition = buildPreviewDefinition(form, flowText);
    const nextDsl = JSON.stringify(definition, null, 2);
    setDslText(nextDsl);
    setPreviewDefinition(definition);
    setDslError(null);
  }

  function compileDslPreview() {
    try {
      const parsed = JSON.parse(dslText) as ScenarioDefinition;
      if (!parsed.id || !parsed.layout || !parsed.logic) {
        setDslError("DSL missing required keys.");
        return;
      }
      setPreviewDefinition(parsed);
      setDslError(null);
    } catch (error) {
      setDslError(error instanceof Error ? error.message : "Invalid DSL.");
    }
  }

  async function handleSaveBlueprint() {
    if (!canSave) return;
    const payload = {
      slug: slugify(form.slug),
      title: form.title.trim(),
      summary: form.summary.trim() || null,
      category: form.category,
      tags: form.tags.split(",").map((item) => item.trim()).filter(Boolean),
      visibility: form.visibility,
      monetization_mode: form.monetization,
      token_price: form.monetization === "paid" ? Number(form.tokenPrice || 0) : null,
      logic_text: dslText.trim(),
      metadata: { builder: "studio-v4" },
    } as const;
    try {
      if (selectedBlueprintId) {
        await patchScenarioBlueprint(selectedBlueprintId, payload);
        setMessage("Blueprint updated (new version recorded).");
      } else {
        const created = await createScenarioBlueprint(payload);
        setSelectedBlueprintId(created.id);
        setMessage("Blueprint created.");
      }
      await reload();
    } catch {
      setMessage("Could not save blueprint.");
    }
  }

  async function handleSelectBlueprint(item: ScenarioBlueprintRead) {
    setSelectedBlueprintId(item.id);
    setForm({
      slug: item.slug,
      title: item.title,
      summary: item.summary ?? "",
      category: (item.category as FormState["category"]) || "growth",
      visibility: item.visibility === "marketplace" ? "public" : ((item.visibility as FormState["visibility"]) || "private"),
      monetization: (item.monetization_mode as FormState["monetization"]) || "free",
      tokenPrice: item.token_price ? String(item.token_price) : "",
      tags: item.tags.join(", "),
    });
    const logicText = (item.logic_text ?? "").trim();
    if (logicText.startsWith("{")) {
      setDslText(logicText);
      compileDslPreview();
    }
    const [versionRows, lineageRow] = await Promise.all([
      fetchScenarioBlueprintVersions(item.id, 12).catch(() => []),
      fetchScenarioBlueprintLineage(item.id).catch(() => null),
    ]);
    setVersions(versionRows);
    setLineage(lineageRow);
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5">
      <section className="pv-panel p-5">
        <p className="pv-kicker">Scenario Platform V4</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-zinc-950">Creator Studio</h1>
        <p className="mt-2 text-sm text-zinc-600">No-code builder, DSL editing, runtime preview, publish, remix, and version tree.</p>
        {message ? <p className="mt-3 text-sm font-semibold text-emerald-700">{message}</p> : null}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <article className="pv-panel p-5">
          <h2 className="text-lg font-semibold text-zinc-950">Builder</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <input value={form.slug} onChange={(event) => setForm((prev) => ({ ...prev, slug: event.target.value }))} className="pv-input" placeholder="slug" />
            <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} className="pv-input" placeholder="title" />
          </div>
          <textarea value={form.summary} onChange={(event) => setForm((prev) => ({ ...prev, summary: event.target.value }))} className="pv-textarea mt-3 min-h-[70px]" placeholder="summary" />
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            <select value={form.category} onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value as FormState["category"] }))} className="pv-input">
              <option value="growth">growth</option><option value="utility">utility</option><option value="learning">learning</option><option value="productivity">productivity</option><option value="entertainment">entertainment</option>
            </select>
            <select value={form.visibility} onChange={(event) => setForm((prev) => ({ ...prev, visibility: event.target.value as FormState["visibility"] }))} className="pv-input">
              <option value="private">private</option><option value="public">public</option><option value="premium">premium</option>
            </select>
            <select value={form.monetization} onChange={(event) => setForm((prev) => ({ ...prev, monetization: event.target.value as FormState["monetization"] }))} className="pv-input">
              <option value="free">free</option><option value="pro_only">pro-only</option><option value="paid">paid</option>
            </select>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <input value={form.tags} onChange={(event) => setForm((prev) => ({ ...prev, tags: event.target.value }))} className="pv-input" placeholder="tags: growth, onboarding" />
            <input value={form.tokenPrice} onChange={(event) => setForm((prev) => ({ ...prev, tokenPrice: event.target.value }))} className="pv-input" placeholder="token price for paid" disabled={form.monetization !== "paid"} />
          </div>
          <textarea value={flowText} onChange={(event) => setFlowText(event.target.value)} className="pv-textarea mt-3 min-h-[90px]" placeholder="No-code flow steps" />
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" className="pv-button-secondary !w-auto" onClick={syncDslFromBuilder}>Sync DSL</button>
            <button type="button" className="pv-button-primary !w-auto" disabled={!canSave} onClick={() => void handleSaveBlueprint()}>{selectedBlueprintId ? "Update" : "Create"}</button>
          </div>
        </article>

        <article className="pv-panel p-5">
          <h2 className="text-lg font-semibold text-zinc-950">DSL + Preview</h2>
          <textarea value={dslText} onChange={(event) => setDslText(event.target.value)} className="pv-textarea mt-3 min-h-[220px] font-mono text-xs" />
          <div className="mt-2 flex flex-wrap gap-2">
            <button type="button" className="pv-button-secondary !w-auto" onClick={compileDslPreview}>Compile preview</button>
          </div>
          {dslError ? <p className="mt-2 text-sm text-rose-700">DSL error: {dslError}</p> : null}
          {previewDefinition ? (
            <div className="mt-3 rounded-[0.9rem] border border-zinc-200 bg-zinc-50/70 p-3">
              <ScenarioAppRuntime definition={previewDefinition} actions={scenarioPlatformActions} />
            </div>
          ) : null}
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">My Blueprints</h3>
          <div className="mt-3 space-y-2">
            {mine.map((item) => (
              <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-[11px] text-zinc-600">v{item.version_number} · used {item.usage_count} · saves {item.save_count}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleSelectBlueprint(item)}>Open</button>
                  <button type="button" className="pv-button-secondary !w-auto" onClick={() => void publishScenarioBlueprint(item.id)}>Publish</button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">Versions</h3>
          <div className="mt-3 space-y-2">
            {versions.map((item) => (
              <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">v{item.version_number}</p>
                <p className="text-xs text-zinc-600">{item.change_note ?? "snapshot"}</p>
              </div>
            ))}
            {!versions.length ? <p className="text-sm text-zinc-600">Select blueprint to load version history.</p> : null}
          </div>
        </article>

        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">Lineage</h3>
          <div className="mt-3 space-y-2">
            {lineage?.chain.map((node) => (
              <div key={node.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">{node.title}</p>
                <p className="text-xs text-zinc-600">{node.slug}</p>
              </div>
            ))}
            {!lineage?.chain.length ? <p className="text-sm text-zinc-600">Lineage tree appears after fork/remix.</p> : null}
          </div>
        </article>
      </section>

      <section className="pv-panel p-4">
        <h3 className="text-base font-semibold text-zinc-950">Marketplace Feed</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {marketplace.map((item) => (
            <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
              <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
              <p className="mt-1 text-[11px] text-zinc-600">by {item.author_display_name ?? item.owner_user_id.slice(0, 8)}</p>
              <p className="mt-1 text-[11px] text-zinc-500">run {item.run_count} · likes {item.like_count} · forks {item.fork_count}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void forkScenarioMarketplaceBlueprint(item.id)}>Fork</button>
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void remixScenarioMarketplaceBlueprint(item.id)}>Remix</button>
                <button type="button" className="pv-button-secondary !w-auto" onClick={() => void likeScenarioMarketplaceBlueprint(item.id)}>Like</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <ScenarioGeneratorLab />
    </div>
  );
}
