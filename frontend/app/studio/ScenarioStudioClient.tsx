"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  advanceScenarioWorkflowRun,
  createScenarioBlueprint,
  createScenarioWorkflow,
  fetchMyScenarioBlueprints,
  fetchMyScenarioWorkflows,
  fetchScenarioMarketplace,
  fetchTeamSharedScenarioBlueprints,
  forkScenarioMarketplaceBlueprint,
  likeScenarioMarketplaceBlueprint,
  publishScenarioBlueprint,
  runScenarioWorkflow,
  shareScenarioBlueprint,
} from "@/lib/client-api";
import type { ScenarioBlueprintRead, ScenarioWorkflowRunRead } from "@/lib/types";

type StudioFormState = {
  slug: string;
  title: string;
  summary: string;
  logicText: string;
};

const INITIAL_FORM: StudioFormState = {
  slug: "",
  title: "",
  summary: "",
  logicText: "",
};

export function ScenarioStudioClient() {
  const [mine, setMine] = useState<ScenarioBlueprintRead[]>([]);
  const [marketplace, setMarketplace] = useState<ScenarioBlueprintRead[]>([]);
  const [shared, setShared] = useState<ScenarioBlueprintRead[]>([]);
  const [workflowIds, setWorkflowIds] = useState<string[]>([]);
  const [latestRun, setLatestRun] = useState<ScenarioWorkflowRunRead | null>(null);
  const [workflowRunId, setWorkflowRunId] = useState<string | null>(null);
  const [form, setForm] = useState<StudioFormState>(INITIAL_FORM);
  const [shareEmail, setShareEmail] = useState("");
  const [selectedBlueprint, setSelectedBlueprint] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const canCreate = useMemo(
    () => form.slug.trim() && form.title.trim() && form.logicText.trim(),
    [form.logicText, form.slug, form.title],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [mineData, marketplaceData, sharedData, workflows] = await Promise.all([
        fetchMyScenarioBlueprints().catch(() => []),
        fetchScenarioMarketplace(18).catch(() => []),
        fetchTeamSharedScenarioBlueprints().catch(() => []),
        fetchMyScenarioWorkflows().catch(() => []),
      ]);
      setMine(mineData);
      setMarketplace(marketplaceData);
      setShared(sharedData);
      setWorkflowIds(workflows.map((workflow) => workflow.id));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function handleCreateBlueprint() {
    if (!canCreate) return;
    try {
      await createScenarioBlueprint({
        slug: form.slug.trim(),
        title: form.title.trim(),
        summary: form.summary.trim() || null,
        logic_text: form.logicText.trim(),
        category: "growth",
        visibility: "private",
      });
      setForm(INITIAL_FORM);
      setMessage("Blueprint created.");
      await reload();
    } catch {
      setMessage("Could not create blueprint.");
    }
  }

  async function handlePublish(blueprintId: string) {
    try {
      const result = await publishScenarioBlueprint(blueprintId);
      setMessage(
        result.creator_reward_applied
          ? `Blueprint published. +${result.creator_reward_tokens} tokens creator reward.`
          : "Blueprint published.",
      );
      await reload();
    } catch {
      setMessage("Could not publish blueprint.");
    }
  }

  async function handleFork(blueprintId: string) {
    try {
      const result = await forkScenarioMarketplaceBlueprint(blueprintId);
      setMessage(
        result.token_spent > 0
          ? `Forked blueprint. Spent ${result.token_spent} tokens.`
          : "Forked blueprint.",
      );
      await reload();
    } catch {
      setMessage("Could not fork blueprint.");
    }
  }

  async function handleLike(blueprintId: string) {
    try {
      await likeScenarioMarketplaceBlueprint(blueprintId);
      setMessage("Liked marketplace blueprint.");
      await reload();
    } catch {
      setMessage("Could not like blueprint.");
    }
  }

  async function handleShare() {
    if (!selectedBlueprint || !shareEmail.trim()) return;
    try {
      await shareScenarioBlueprint(selectedBlueprint, {
        member_email: shareEmail.trim(),
        can_edit: true,
      });
      setMessage("Blueprint shared with teammate.");
      setShareEmail("");
      await reload();
    } catch {
      setMessage("Could not share blueprint.");
    }
  }

  async function handleCreateWorkflow(blueprintId: string) {
    try {
      const workflow = await createScenarioWorkflow({
        name: `Flow for ${blueprintId.slice(0, 6)}`,
        description: "Auto-created from studio",
        step_blueprint_ids: [blueprintId],
        visibility: "private",
      });
      setMessage("Workflow created.");
      setWorkflowIds((prev) => [workflow.id, ...prev]);
    } catch {
      setMessage("Could not create workflow.");
    }
  }

  async function handleRunWorkflow(workflowId: string) {
    try {
      const run = await runScenarioWorkflow(workflowId, { context: { source: "studio" } });
      setWorkflowRunId(run.id);
      setLatestRun(run);
      setMessage("Workflow run started.");
    } catch {
      setMessage("Could not run workflow.");
    }
  }

  async function handleAdvanceWorkflow() {
    if (!workflowRunId) return;
    try {
      const advanced = await advanceScenarioWorkflowRun(workflowRunId);
      setLatestRun(advanced.run);
      setMessage(advanced.is_completed ? "Workflow completed." : "Workflow advanced.");
    } catch {
      setMessage("Could not advance workflow.");
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <section className="pv-panel p-5">
        <p className="pv-kicker">Scenario Studio</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-zinc-950">
          Build, publish, and scale AI scenarios.
        </h1>
        <p className="mt-2 text-sm text-zinc-600">
          Create user-generated scenarios, publish to marketplace, share with team, and run workflow chains.
        </p>
        {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
      </section>

      <section className="pv-panel p-5">
        <h2 className="text-lg font-semibold text-zinc-950">Create Blueprint</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <input
            value={form.slug}
            onChange={(event) => setForm((prev) => ({ ...prev, slug: event.target.value }))}
            className="pv-input"
            placeholder="slug (e.g. growth-qa-sprint)"
          />
          <input
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            className="pv-input"
            placeholder="Scenario title"
          />
        </div>
        <textarea
          value={form.summary}
          onChange={(event) => setForm((prev) => ({ ...prev, summary: event.target.value }))}
          className="pv-textarea mt-3 min-h-[80px]"
          placeholder="Short summary"
        />
        <textarea
          value={form.logicText}
          onChange={(event) => setForm((prev) => ({ ...prev, logicText: event.target.value }))}
          className="pv-textarea mt-3 min-h-[120px]"
          placeholder="Scenario logic blueprint"
        />
        <button type="button" className="pv-button-primary mt-3 !w-auto" disabled={!canCreate} onClick={() => void handleCreateBlueprint()}>
          Save Blueprint
        </button>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">My Blueprints</h3>
          <div className="mt-3 space-y-2">
            {mine.map((item) => (
              <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs text-zinc-600">{item.slug}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handlePublish(item.id)}>
                    Publish
                  </button>
                  <button type="button" className="pv-button-secondary !w-auto" onClick={() => void handleCreateWorkflow(item.id)}>
                    Workflow
                  </button>
                  <button type="button" className="pv-button-secondary !w-auto" onClick={() => setSelectedBlueprint(item.id)}>
                    Share
                  </button>
                </div>
              </div>
            ))}
            {!mine.length && !loading ? <p className="text-sm text-zinc-600">No blueprints yet.</p> : null}
          </div>
        </article>

        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">Marketplace</h3>
          <div className="mt-3 space-y-2">
            {marketplace.map((item) => (
              <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs text-zinc-600">
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
              </div>
            ))}
            {!marketplace.length && !loading ? <p className="text-sm text-zinc-600">Marketplace is empty.</p> : null}
          </div>
        </article>

        <article className="pv-panel p-4">
          <h3 className="text-base font-semibold text-zinc-950">Team Shared</h3>
          {selectedBlueprint ? (
            <div className="mt-3 rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
              <p className="text-xs text-zinc-600">Share selected blueprint</p>
              <input
                value={shareEmail}
                onChange={(event) => setShareEmail(event.target.value)}
                className="pv-input mt-2"
                placeholder="teammate email"
              />
              <button type="button" className="pv-button-primary mt-2 !w-auto" onClick={() => void handleShare()}>
                Send Share
              </button>
            </div>
          ) : null}
          <div className="mt-3 space-y-2">
            {shared.map((item) => (
              <div key={item.id} className="rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs text-zinc-600">{item.slug}</p>
              </div>
            ))}
            {!shared.length && !loading ? <p className="text-sm text-zinc-600">No shared scenarios yet.</p> : null}
          </div>
        </article>
      </section>

      <section className="pv-panel p-4">
        <h3 className="text-base font-semibold text-zinc-950">Workflow Runs</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {workflowIds.map((workflowId) => (
            <button key={workflowId} type="button" className="pv-button-secondary !w-auto" onClick={() => void handleRunWorkflow(workflowId)}>
              Run {workflowId.slice(0, 6)}
            </button>
          ))}
          {workflowRunId ? (
            <button type="button" className="pv-button-primary !w-auto" onClick={() => void handleAdvanceWorkflow()}>
              Advance Run
            </button>
          ) : null}
        </div>
        {latestRun ? (
          <p className="mt-2 text-sm text-zinc-700">
            Run status: {latestRun.status}, step {latestRun.current_step}/{latestRun.total_steps}
          </p>
        ) : (
          <p className="mt-2 text-sm text-zinc-600">Start a workflow run to see multi-step execution state.</p>
        )}
      </section>
    </div>
  );
}
