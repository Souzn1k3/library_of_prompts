import { renderHook, waitFor, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useHomeWorkbenchState } from "@/app/home-workbench/useHomeWorkbenchState";
import type { PromptListItem } from "@/lib/types";

function createPrompt(input: Partial<PromptListItem> & Pick<PromptListItem, "id" | "slug" | "title">): PromptListItem {
  return {
    id: input.id,
    slug: input.slug,
    title: input.title,
    summary: input.summary ?? "summary",
    status: "published",
    technique: input.technique ?? "other",
    moderation_state: "approved",
    category_id: "cat-1",
    author_id: null,
    created_at: new Date().toISOString(),
    use_cases: input.use_cases ?? [],
    tags: input.tags ?? [],
    quality_score: input.quality_score ?? 80,
    save_count: input.save_count ?? 0,
    copy_count: input.copy_count ?? 0,
  };
}

describe("useHomeWorkbenchState", () => {
  it("supports selection/filter flow and keeps explorer state cohesive", async () => {
    const prompts: PromptListItem[] = [
      createPrompt({
        id: "1",
        slug: "launch-plan",
        title: "Launch plan",
        use_cases: ["launch planning"],
      }),
      createPrompt({
        id: "2",
        slug: "api-debug",
        title: "API debugging",
        use_cases: ["debugging"],
      }),
    ];

    const { result } = renderHook(() =>
      useHomeWorkbenchState({
        prompts,
        quickUseCases: ["launch planning", "debugging"],
        heroPromptBody: null,
        language: "en",
      }),
    );

    expect(result.current.selectedPrompt?.slug).toBe("launch-plan");

    act(() => {
      result.current.setQuery("API");
    });

    await waitFor(() => {
      expect(result.current.explorer.filteredScenarios.length).toBeGreaterThan(0);
      expect(result.current.selectedPrompt?.slug).toBe("api-debug");
    });

    act(() => {
      result.current.toggleFacet("debugging");
    });
    expect(result.current.selectedFacet).toBe("debugging");

    act(() => {
      result.current.resetFilters();
    });
    expect(result.current.query).toBe("");
    expect(result.current.selectedFacet).toBeNull();
    expect(result.current.selectedTechnique).toBe("all");
  });
});

