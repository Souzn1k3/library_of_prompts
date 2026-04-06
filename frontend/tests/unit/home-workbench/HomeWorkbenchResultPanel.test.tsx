import React from "react";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HomeWorkbenchResultPanel } from "@/app/home-workbench/HomeWorkbenchResultPanel";
import type { ScenarioDefinition } from "@/features/scenarios/domain/scenario";
import type { PromptListItem } from "@/lib/types";

const t = (key: string, params?: Record<string, string | number | null | undefined>) =>
  params?.count !== undefined ? `${key}:${params.count}` : key;

function createScenario(): ScenarioDefinition {
  return {
    id: "scenario-1",
    slug: "scenario-1",
    title: "Scenario One",
    summary: "Summary",
    technique: "other",
    category: "utility",
    facets: ["Debug"],
    qualityScore: 80,
    saveCount: 4,
    copyCount: 2,
    access: {
      freePreviewEnabled: true,
      freeRunsPerDay: 3,
      fullBlueprintRequiresPro: true,
      proCapabilities: ["Save"],
    },
    retention: {
      replayReason: "repeat",
      nextScenarioSlug: null,
      unfinishedActionHint: "resume",
    },
  };
}

function createPrompt(): PromptListItem {
  return {
    id: "prompt-1",
    slug: "scenario-1",
    title: "Scenario One",
    summary: "Summary",
    status: "published",
    technique: "other",
    moderation_state: "approved",
    category_id: "cat",
    author_id: null,
    created_at: new Date().toISOString(),
  };
}

describe("HomeWorkbenchResultPanel", () => {
  it("renders fallback null state when no scenario is selected", () => {
    const { container } = render(
      <HomeWorkbenchResultPanel
        t={t as never}
        selectedScenario={null}
        selectedPrompt={null}
        liveResult=""
        taskInput=""
        onTaskInputChange={vi.fn()}
        onTaskInputBlur={vi.fn()}
        hasCurrentUnfinished={false}
        outputDepth="detailed"
        onOutputDepthChange={vi.fn()}
        onRunNow={vi.fn()}
        runPending={false}
        onPurchaseBoost={vi.fn()}
        boostPending={false}
        openScenarioHref="/prompt/scenario-1"
        onCopy={vi.fn()}
        onToggleSave={vi.fn()}
        onShare={vi.fn()}
        copyState="idle"
        shareState="idle"
        isSaved={false}
        engagementMessage={null}
        runGuardMessage={null}
        lastRunAt={null}
        demoStatus={{ isPro: false, remainingRuns: 3, capReached: false, bonusRunsRemaining: 0 }}
        unfinished={[]}
        recentSlugs={[]}
        promptBySlug={new Map()}
        onResumeUnfinished={vi.fn()}
        onSelectRecent={vi.fn()}
        onMarkDone={vi.fn()}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows run-cap state, continuity blocks, and action callbacks", () => {
    const onRunNow = vi.fn();
    const onToggleSave = vi.fn();
    const onResume = vi.fn();
    const onSelectRecent = vi.fn();

    const scenario = createScenario();
    const prompt = createPrompt();
    render(
      <HomeWorkbenchResultPanel
        t={t as never}
        selectedScenario={scenario}
        selectedPrompt={prompt}
        liveResult="Generated output"
        taskInput="my task"
        onTaskInputChange={vi.fn()}
        onTaskInputBlur={vi.fn()}
        hasCurrentUnfinished={true}
        outputDepth="detailed"
        onOutputDepthChange={vi.fn()}
        onRunNow={onRunNow}
        runPending={false}
        onPurchaseBoost={vi.fn()}
        boostPending={false}
        openScenarioHref="/prompt/scenario-1"
        onCopy={vi.fn()}
        onToggleSave={onToggleSave}
        onShare={vi.fn()}
        copyState="idle"
        shareState="idle"
        isSaved={false}
        engagementMessage={null}
        runGuardMessage="free_demo_cap_reached"
        lastRunAt={null}
        demoStatus={{ isPro: false, remainingRuns: 0, capReached: true, bonusRunsRemaining: 0 }}
        unfinished={[{ slug: "scenario-1", task: "Fix onboarding funnel", updatedAt: new Date().toISOString() }]}
        recentSlugs={["scenario-1"]}
        promptBySlug={new Map([["scenario-1", prompt]])}
        onResumeUnfinished={onResume}
        onSelectRecent={onSelectRecent}
        onMarkDone={vi.fn()}
      />,
    );

    expect(screen.getAllByText("home.entryDemoCapReached").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "home.entryRunNow" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "home.entrySaveAction" }));
    expect(onToggleSave).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "home.entryUnfinishedResume" }));
    expect(onResume).toHaveBeenCalledWith("scenario-1", "Fix onboarding funnel");

    fireEvent.click(screen.getByRole("button", { name: "Scenario One" }));
    expect(onSelectRecent).toHaveBeenCalledWith("scenario-1");
  });
});
