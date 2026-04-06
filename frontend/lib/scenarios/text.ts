import type { Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";
import { buildScenarioLiveResult, isRuFamilyLanguage } from "@/features/scenarios/application/scenarioRuntime";
import { mapPromptToScenario } from "@/features/scenarios/infrastructure/promptScenarioMapper";

export { isRuFamilyLanguage };

export function buildPromptFallbackTemplate(language: Language, prompt: PromptListItem): string {
  const isRuFamily = isRuFamilyLanguage(language);
  const promptSummary = prompt.summary?.trim() || (isRuFamily ? "Нет краткого описания." : "No summary provided.");

  if (isRuFamily) {
    return [
      `Контекст: ${prompt.title}`,
      `Описание: ${promptSummary}`,
      "",
      "Сделай:",
      "1) Сначала уточни недостающие детали задачи.",
      "2) Предложи рабочую структуру решения.",
      "3) Дай финальный результат в практичном формате.",
    ].join("\n");
  }

  return [
    `Context: ${prompt.title}`,
    `Summary: ${promptSummary}`,
    "",
    "Do this:",
    "1) Ask for missing details first.",
    "2) Propose a practical solution structure.",
    "3) Return a ready-to-use final output.",
  ].join("\n");
}

export function buildReadyScenarioScript(language: Language, baseScript: string, taskInput: string): string {
  const normalizedTask = taskInput.trim();
  if (!normalizedTask) {
    return baseScript;
  }

  if (isRuFamilyLanguage(language)) {
    return [
      `Задача: ${normalizedTask}`,
      "",
      "Используй шаблон ниже и адаптируй его под эту задачу.",
      "",
      baseScript,
    ].join("\n");
  }

  return [
    `Task: ${normalizedTask}`,
    "",
    "Use the template below and adapt it to this task.",
    "",
    baseScript,
  ].join("\n");
}

export function buildScenarioOutputPreview(
  language: Language,
  prompt: PromptListItem,
  userInput: string,
): string {
  const scenario = mapPromptToScenario(prompt);
  return buildScenarioLiveResult({
    language,
    scenario,
    taskInput: userInput,
    outputDepth: "detailed",
  });
}

export function formatScenarioFacetLabel(value: string): string {
  return value
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}
