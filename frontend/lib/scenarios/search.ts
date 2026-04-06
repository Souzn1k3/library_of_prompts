import type { PromptListItem } from "@/lib/types";

export function normalizeSearchValue(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function promptMatchesUseCase(prompt: PromptListItem, normalizedUseCase: string): boolean {
  const value = [
    ...(prompt.use_cases ?? []),
    ...(prompt.tags ?? []),
    prompt.title,
    prompt.summary ?? "",
  ]
    .join(" ")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ");

  return value.includes(normalizedUseCase);
}

export function scorePrompt(prompt: PromptListItem, normalizedQuery: string): number {
  const title = normalizeSearchValue(prompt.title);
  const summary = normalizeSearchValue(prompt.summary);
  const useCases = normalizeSearchValue((prompt.use_cases ?? []).join(" "));
  const tags = normalizeSearchValue((prompt.tags ?? []).join(" "));

  let score = 0;
  if (title.includes(normalizedQuery)) {
    score += 8;
  }
  if (summary.includes(normalizedQuery)) {
    score += 5;
  }
  if (useCases.includes(normalizedQuery)) {
    score += 4;
  }
  if (tags.includes(normalizedQuery)) {
    score += 3;
  }

  const queryWords = normalizedQuery.split(" ").filter(Boolean);
  for (const word of queryWords) {
    if (title.includes(word)) {
      score += 2;
    }
    if (summary.includes(word)) {
      score += 1;
    }
  }

  return score;
}
