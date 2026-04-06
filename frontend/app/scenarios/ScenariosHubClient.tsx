"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useScenarioWorkspace } from "@/features/scenarios/presentation/useScenarioWorkspace";
import type {
  PromptListItem,
  ScenarioLoopHintsRead,
  ScenarioNextStepRead,
} from "@/lib/types";

type ScenariosHubClientProps = {
  prompts: PromptListItem[];
  nextSteps: ScenarioNextStepRead[];
  loopHints: ScenarioLoopHintsRead | null;
  isAuthenticated: boolean;
};

export function ScenariosHubClient({
  prompts,
  nextSteps,
  loopHints,
  isAuthenticated,
}: ScenariosHubClientProps) {
  const workspace = useScenarioWorkspace();

  const promptBySlug = useMemo(() => {
    const map = new Map<string, PromptListItem>();
    for (const prompt of prompts) {
      map.set(prompt.slug, prompt);
    }
    return map;
  }, [prompts]);

  const featuredPrompts = prompts.slice(0, 6);
  const unfinished = workspace.unfinished.slice(0, 4);
  const recent = workspace.recentSlugs.slice(0, 8);
  const saved = workspace.savedSlugs.slice(0, 8);
  const loopSteps = loopHints?.core_loop_steps ?? [
    "discover_scenario",
    "run_scenario",
    "save_or_share",
    "resume_and_repeat",
    "upgrade_for_full_blueprint",
  ];

  return (
    <div className="space-y-5">
      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Discover and run scenarios</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Start from a proven prompt, run on your own task, then save and resume from workspace.
          </p>
        </div>
        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          {featuredPrompts.length ? (
            featuredPrompts.map((prompt) => (
              <article key={prompt.id} className="pv-card flex h-full flex-col p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  {(prompt.technique ?? "scenario").replaceAll("_", " ")}
                </p>
                <p className="mt-2 text-sm font-semibold text-zinc-900">{prompt.title}</p>
                <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-zinc-600">{prompt.summary ?? "Open this scenario and run it on your data."}</p>
                <div className="mt-auto flex flex-wrap gap-2 pt-3">
                  <Link href={`/?resume=${encodeURIComponent(prompt.slug)}#home-workbench`} className="pv-button-primary !w-auto">
                    Run now
                  </Link>
                  <Link href={`/prompt/${encodeURIComponent(prompt.slug)}`} className="pv-button-secondary !w-auto">
                    Open scenario
                  </Link>
                </div>
              </article>
            ))
          ) : (
            <div className="pv-empty-state lg:col-span-3">
              <p className="text-sm text-zinc-600">No scenarios available yet. Open catalog to start the first run.</p>
            </div>
          )}
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Resume and repeat</h2>
            <p className="mt-2 text-sm text-zinc-600">
              Continue unfinished tasks and keep momentum after reload.
            </p>
          </div>
          <Link href="/#home-workbench" className="pv-inline-link">
            Open workbench
            <span aria-hidden="true">↗</span>
          </Link>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <article className="rounded-[1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">Unfinished</p>
            <div className="mt-3 space-y-2">
              {unfinished.length ? (
                unfinished.map((item) => {
                  const prompt = promptBySlug.get(item.slug);
                  return (
                    <div key={`unfinished-${item.slug}`} className="rounded-[0.85rem] border border-zinc-200 bg-white p-3">
                      <p className="text-sm font-semibold text-zinc-900">{prompt?.title ?? item.slug}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-zinc-600">{item.task}</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Link href={`/?resume=${encodeURIComponent(item.slug)}#home-workbench`} className="pv-button-primary !w-auto !px-3 !py-1.5 !text-xs">
                          Resume run
                        </Link>
                        <Link href={`/prompt/${encodeURIComponent(item.slug)}`} className="pv-button-secondary !w-auto !px-3 !py-1.5 !text-xs">
                          Open scenario
                        </Link>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-zinc-600">No unfinished tasks yet. Start a run and save context to continue later.</p>
              )}
            </div>
          </article>

          <article className="rounded-[1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">Recent & saved</p>
            <div className="mt-3 space-y-3">
              <div>
                <p className="text-xs font-semibold text-zinc-700">Recent</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {recent.length ? recent.map((slug) => (
                    <Link key={`recent-${slug}`} href={`/prompt/${encodeURIComponent(slug)}`} className="pv-segment-pill">
                      {promptBySlug.get(slug)?.title ?? slug}
                    </Link>
                  )) : <p className="text-xs text-zinc-500">No recent scenarios yet.</p>}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-zinc-700">Saved</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {saved.length ? saved.map((slug) => (
                    <Link key={`saved-${slug}`} href={`/prompt/${encodeURIComponent(slug)}`} className="pv-segment-pill pv-segment-pill-active">
                      {promptBySlug.get(slug)?.title ?? slug}
                    </Link>
                  )) : <p className="text-xs text-zinc-500">No saved scenarios yet.</p>}
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-copy">
          <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">Next best step</h2>
          <p className="mt-2 text-sm text-zinc-600">
            Keep the loop active: {loopSteps.join(" → ")}.
          </p>
        </div>
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          <article className="rounded-[1rem] border border-zinc-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">Recommended transitions</p>
            <div className="mt-3 space-y-2">
              {nextSteps.length ? (
                nextSteps.slice(0, 4).map((step) => (
                  <Link
                    key={`${step.source_prompt_slug}:${step.next_prompt_slug}`}
                    href={`/prompt/${encodeURIComponent(step.next_prompt_slug)}`}
                    className="block rounded-[0.8rem] border border-zinc-200 bg-zinc-50 p-3"
                  >
                    <p className="text-sm font-semibold text-zinc-900">{step.next_prompt_slug}</p>
                    <p className="mt-1 text-xs text-zinc-600">{step.reason}</p>
                  </Link>
                ))
              ) : (
                <p className="text-sm text-zinc-600">Run your first scenario to unlock personalized next-step chain.</p>
              )}
            </div>
          </article>

          <article className="rounded-[1rem] border border-zinc-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(245,248,255,0.9))] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">Upgrade path</p>
            <p className="mt-3 text-sm text-zinc-700">
              Free demo runs per scenario: {loopHints?.free_demo_runs_per_scenario ?? 3}. Upgrade to unlock full blueprint and unlimited execution.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">
                Upgrade to PRO
              </Link>
              <Link href={isAuthenticated ? "/dashboard" : "/signup"} className="pv-button-secondary !w-auto">
                {isAuthenticated ? "Open dashboard" : "Create account"}
              </Link>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
