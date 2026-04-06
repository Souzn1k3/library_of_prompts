import type { Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

export function isRuFamilyLanguage(language: Language): boolean {
  return language === "ru" || language === "tt";
}

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
  const isRuFamily = isRuFamilyLanguage(language);
  const task = userInput.trim();
  const summary = prompt.summary?.trim() || (isRuFamily ? "Описание сценария отсутствует." : "No scenario summary.");

  if (isRuFamily) {
    return [
      "Результат AI-сценария:",
      "",
      `Сценарий: ${prompt.title}`,
      `Фокус: ${task || summary}`,
      "",
      "1) Диагноз ситуации и ключевые риски",
      "2) Пошаговый план действий на ближайший цикл",
      "3) Готовый формат ответа, который можно сразу применять",
    ].join("\n");
  }

  return [
    "AI scenario output:",
    "",
    `Scenario: ${prompt.title}`,
    `Focus: ${task || summary}`,
    "",
    "1) Situation diagnosis and key risks",
    "2) Action plan for the next execution cycle",
    "3) Ready-to-use output format you can run immediately",
  ].join("\n");
}

export function formatScenarioFacetLabel(value: string): string {
  return value
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}
