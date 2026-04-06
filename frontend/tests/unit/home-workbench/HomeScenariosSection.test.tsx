import React from "react";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HomeScenariosSection } from "@/app/HomeScenariosSection";

vi.mock("@/components/i18n/LanguageProvider", () => ({
  useI18n: () => ({
    language: "en",
    t: (key: string) => key,
  }),
}));

vi.mock("@/features/scenarios/presentation/useScenarioGameLedger", () => ({
  useScenarioGameLedger: () => ({
    gameState: { pending_tokens: 0, claimable_tokens: 0 },
    earnPending: false,
    claimPending: false,
    latestMessage: null,
    earn: vi.fn(async () => null),
    claim: vi.fn(async () => null),
  }),
}));

vi.mock("@/lib/analytics", () => ({
  trackEvent: vi.fn(),
}));

const prompt = {
  id: "prompt-1",
  slug: "prompt-1",
  title: "Prompt one",
  summary: "summary",
  status: "published",
  technique: "other",
  moderation_state: "approved",
  category_id: "cat-1",
  author_id: null,
  created_at: new Date().toISOString(),
};

describe("HomeScenariosSection", () => {
  it("renders packs, next steps, showcase, and pricing blocks", () => {
    render(
      <HomeScenariosSection
        prompts={[prompt]}
        recommendedPrompts={[prompt]}
        retentionPrompts={[prompt]}
        packs={[
          {
            id: "pack-a",
            title: "Pack A",
            description: "Description",
            outcome: "Outcome",
            prompt_slugs: [prompt.slug],
            prompts: [prompt],
            cta_prompt_slug: prompt.slug,
          },
        ]}
        chains={[
          {
            id: "chain-a",
            title: "Chain A",
            description: "desc",
            steps: [{ position: 1, prompt_slug: prompt.slug, title: prompt.title, goal: "Goal" }],
          },
        ]}
        nextSteps={[
          {
            source_prompt_slug: prompt.slug,
            next_prompt_slug: prompt.slug,
            reason: "Next reason",
            confidence: 0.9,
          },
        ]}
        returnTriggers={[
          {
            trigger_key: "unfinished_runs",
            label: "Resume items",
            count: 2,
            href: "/dashboard",
          },
        ]}
        showcase={[
          {
            share_id: "share-1",
            prompt_slug: prompt.slug,
            blueprint_id: null,
            title: "Showcase title",
            excerpt: "Showcase excerpt",
            output_preview: "Preview output",
            visibility: "public",
            upvotes: 2,
            created_at: new Date().toISOString(),
          },
        ]}
        pricingPlans={[
          {
            tier: "free",
            price_monthly_usd: 0,
            headline: "Start free",
            highlights: [],
          },
        ]}
        initialAuthenticated={false}
      />,
    );

    expect(screen.getByText("Pack A")).toBeInTheDocument();
    expect(screen.getByText("Next reason")).toBeInTheDocument();
    expect(screen.getByText("Showcase title")).toBeInTheDocument();
    expect(screen.getByText("$0")).toBeInTheDocument();

    expect(screen.getByRole("link", { name: /home.packAction/ })).toHaveAttribute(
      "href",
      `/prompt/${prompt.slug}`,
    );
  });
});
