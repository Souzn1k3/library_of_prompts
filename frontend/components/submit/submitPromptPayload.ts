"use client";

import { submitPrompt } from "@/lib/client-api";

export type SubmitPromptPayload = Parameters<typeof submitPrompt>[0];

export type SubmitPromptSelections = {
  selectedUseCases: string[];
  selectedModels: string[];
  selectedTags: string[];
};

function stringValue(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "");
}

function stringOrNull(formData: FormData, key: string): string | null {
  const value = stringValue(formData, key).trim();
  return value.length > 0 ? value : null;
}

function stringList(formData: FormData, key: string): string[] {
  return formData.getAll(key).map((value) => String(value));
}

function parseDifficulty(value: string): SubmitPromptPayload["difficulty"] {
  if (value === "beginner" || value === "intermediate" || value === "advanced") {
    return value;
  }
  return null;
}

function parseOutputType(value: string): SubmitPromptPayload["output_type"] {
  if (value === "text" || value === "code" || value === "structured") {
    return value;
  }
  return null;
}

export function buildSubmitPayload(formData: FormData): {
  payload: SubmitPromptPayload;
  selections: SubmitPromptSelections;
} {
  const selectedUseCases = stringList(formData, "use_cases");
  const selectedModels = stringList(formData, "model_compatibility");
  const selectedTags = stringList(formData, "tags");
  const parsedPrice = Number(stringValue(formData, "price_rub"));

  return {
    payload: {
      slug: stringValue(formData, "slug"),
      title: stringValue(formData, "title"),
      body: stringValue(formData, "body"),
      summary: stringOrNull(formData, "summary"),
      category_id: stringValue(formData, "category_id"),
      technique: stringValue(formData, "technique") || "other",
      difficulty: parseDifficulty(stringValue(formData, "difficulty")),
      output_type: parseOutputType(stringValue(formData, "output_type")),
      use_cases: selectedUseCases,
      model_compatibility: selectedModels,
      tags: selectedTags,
      price_rub: parsedPrice || null,
    },
    selections: {
      selectedUseCases,
      selectedModels,
      selectedTags,
    },
  };
}
