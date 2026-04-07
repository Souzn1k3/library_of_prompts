import type { Language } from "@/lib/i18n";

import type { ScenarioDefinition, ScenarioResultDepth } from "../domain/scenario";

export function isRuFamilyLanguage(language: Language): boolean {
  return language === "ru" || language === "tt";
}

export function buildScenarioLiveResult(params: {
  language: Language;
  scenario: Pick<ScenarioDefinition, "title" | "summary" | "category">;
  taskInput: string;
  outputDepth: ScenarioResultDepth;
  variationSeed?: number;
}): string {
  const { language, scenario, taskInput, outputDepth, variationSeed = 0 } = params;
  const isRuFamily = isRuFamilyLanguage(language);
  const focus = taskInput.trim() || scenario.summary;
  const variantIndex = Math.abs(variationSeed) % 3;

  const variantByLanguage = isRuFamily
    ? [
        "Версия A: акцент на диагностику.",
        "Версия B: акцент на скорость выполнения.",
        "Версия C: акцент на снижение риска.",
      ]
    : [
        "Variant A: diagnosis-first.",
        "Variant B: speed-first.",
        "Variant C: risk-control first.",
      ];

  const categoryLabel = isRuFamily ? scenarioCategoryRu(scenario.category) : scenario.category;
  const variant = variantByLanguage[variantIndex] ?? variantByLanguage[0];

  if (isRuFamily) {
    if (outputDepth === "concise") {
      return [
        "Результат AI-промпта:",
        "",
        `Промпт: ${scenario.title}`,
        `Категория: ${categoryLabel}`,
        `Фокус: ${focus}`,
        variant,
        "",
        "• Итог: есть рабочий результат для запуска без дополнительных шагов",
        "• Следующий шаг: откройте промпт и примените к вашим данным",
        "• Метрика: ценность за первые 10 минут выполнения",
      ].join("\n");
    }

    return [
      "Результат AI-промпта:",
      "",
      `Промпт: ${scenario.title}`,
      `Категория: ${categoryLabel}`,
      `Фокус: ${focus}`,
      variant,
      "",
      "1) Диагностика контекста",
      "Определены ключевые ограничения, точки роста и риски.",
      "",
      "2) План выполнения",
      "- Подтвердить входные параметры",
      "- Запустить базовый промпт",
      "- Зафиксировать результат в повторяемый шаблон",
      "",
      "3) Готовый output",
      "Выход структурирован так, чтобы его можно было сразу применять в работе.",
    ].join("\n");
  }

  if (outputDepth === "concise") {
    return [
      "AI prompt result:",
      "",
      `Prompt: ${scenario.title}`,
      `Category: ${categoryLabel}`,
      `Focus: ${focus}`,
      variant,
      "",
      "• Outcome: execution-ready output with no extra setup",
      "• Next step: open and run the full prompt",
      "• Metric: tangible value in the first 10 minutes",
    ].join("\n");
  }

  return [
    "AI prompt result:",
    "",
    `Prompt: ${scenario.title}`,
    `Category: ${categoryLabel}`,
    `Focus: ${focus}`,
    variant,
    "",
    "1) Context diagnosis",
    "Key constraints, leverage points, and risks are surfaced.",
    "",
    "2) Execution plan",
    "- Confirm missing inputs",
    "- Run the base prompt",
    "- Convert result into a reusable workflow",
    "",
    "3) Ready output",
    "The output is structured for immediate team use.",
  ].join("\n");
}

function scenarioCategoryRu(category: ScenarioDefinition["category"]): string {
  switch (category) {
    case "utility":
      return "Практика";
    case "learning":
      return "Обучение";
    case "productivity":
      return "Продуктивность";
    case "entertainment":
      return "Развлечение";
    case "growth":
      return "Рост";
    default:
      return "Промпт";
  }
}
