import type { LessonListItem, PromptListItem } from "@/lib/types";

function tokenize(value: string): Set<string> {
  return new Set(
    value
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter((chunk) => chunk.length >= 3),
  );
}

export function pickRelatedLessonsForPrompts<T extends LessonListItem>(
  prompts: PromptListItem[],
  lessons: T[],
  limit = 4,
): T[] {
  const promptTokens = new Set<string>();
  for (const prompt of prompts) {
    for (const token of tokenize(`${prompt.title} ${prompt.summary ?? ""}`)) {
      promptTokens.add(token);
    }
  }

  const scored = lessons.map((lesson) => {
    const lessonTokens = tokenize(lesson.title);
    let overlap = 0;
    for (const token of lessonTokens) {
      if (promptTokens.has(token)) overlap += 1;
    }
    return { lesson, overlap };
  });

  return scored
    .sort((a, b) => b.overlap - a.overlap)
    .slice(0, limit)
    .map((row) => row.lesson);
}
