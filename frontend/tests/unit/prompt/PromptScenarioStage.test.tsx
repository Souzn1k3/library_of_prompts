import React from "react";

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PromptScenarioStage } from "@/app/prompt/[slug]/PromptScenarioStage";
import type { PromptDetail } from "@/lib/types";

type DemoRunMockState = {
  runPending: boolean;
  capReached: boolean;
  isPro: boolean;
  remainingRuns: number | null;
  latestMessage: string | null;
};

const mockState: DemoRunMockState = {
  runPending: false,
  capReached: false,
  isPro: false,
  remainingRuns: 3,
  latestMessage: null,
};
const runSpy = vi.fn(async () => ({ executed: true, status: { cap_reached: false } }));

vi.mock("@/features/scenarios/presentation/useScenarioDemoRun", () => ({
  useScenarioDemoRun: () => ({
    ...mockState,
    run: runSpy,
  }),
}));

function createPrompt(overrides?: Partial<PromptDetail>): PromptDetail {
  return {
    id: "prompt-1",
    slug: "scenario-stage",
    title: "Scenario Stage",
    summary: "Summary",
    status: "published",
    technique: "other",
    moderation_state: "approved",
    category_id: "cat-1",
    author_id: null,
    created_at: new Date().toISOString(),
    body: "Prompt body",
    body_locked: true,
    ...overrides,
  };
}

describe("PromptScenarioStage", () => {
  beforeEach(() => {
    runSpy.mockClear();
    mockState.runPending = false;
    mockState.capReached = false;
    mockState.isPro = false;
    mockState.remainingRuns = 3;
    mockState.latestMessage = null;
  });

  it("renders locked pro-gate state with unlock CTA for free users", () => {
    render(<PromptScenarioStage language="en" prompt={createPrompt({ body_locked: true })} />);

    expect(screen.getByText("Full scenario is locked")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Unlock scenario (PRO)" })).toHaveAttribute(
      "href",
      "/pricing?tier=starter",
    );
  });

  it("renders cap reached state and disables run actions", () => {
    mockState.capReached = true;
    mockState.remainingRuns = 0;
    mockState.latestMessage = "free_demo_cap_reached";

    render(<PromptScenarioStage language="en" prompt={createPrompt({ body_locked: false })} />);

    expect(screen.getAllByText("Demo run cap reached. Upgrade to PRO.").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Run scenario" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Refresh output" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Run scenario" }));
    expect(runSpy).not.toHaveBeenCalled();
  });
});
