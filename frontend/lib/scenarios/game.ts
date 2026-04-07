export type ScenarioGameChoice = {
  en: string;
  ru: string;
  reward: number;
  feedbackEn: string;
  feedbackRu: string;
};

export type ScenarioGameChallenge = {
  id: string;
  promptEn: string;
  promptRu: string;
  choices: ScenarioGameChoice[];
};

export const SCENARIO_GAME_CHALLENGES: ScenarioGameChallenge[] = [
  {
    id: "challenge-1",
    promptEn: "You need better bug reports from your team. Pick the strongest AI instruction.",
    promptRu: "Нужно улучшить баг-репорты в команде. Выбери самый сильный AI-инструктаж.",
    choices: [
      {
        en: "Write any bug report.",
        ru: "Напиши любой баг-репорт.",
        reward: 1,
        feedbackEn: "Too vague. The model has no structure to follow.",
        feedbackRu: "Слишком расплывчато. У модели нет структуры для ответа.",
      },
      {
        en: "Create a bug report with steps, expected behavior, actual behavior, impact, and logs.",
        ru: "Собери баг-репорт: шаги, ожидаемое, фактическое, влияние и логи.",
        reward: 6,
        feedbackEn: "Great. Clear structure = stable output quality.",
        feedbackRu: "Отлично. Четкая структура дает стабильный результат.",
      },
      {
        en: "Explain why bugs are bad.",
        ru: "Объясни, почему баги — это плохо.",
        reward: 2,
        feedbackEn: "Helpful but not actionable for real execution.",
        feedbackRu: "Полезно, но не дает рабочего результата.",
      },
    ],
  },
  {
    id: "challenge-2",
    promptEn: "You need a launch plan in 24 hours. Choose the highest-leverage prompt.",
    promptRu: "Нужен план запуска за 24 часа. Выбери промпт с максимальной пользой.",
    choices: [
      {
        en: "Give random launch ideas.",
        ru: "Дай случайные идеи запуска.",
        reward: 1,
        feedbackEn: "No timeline, no owners, no execution path.",
        feedbackRu: "Нет сроков, владельцев и пути исполнения.",
      },
      {
        en: "Build a 24-hour launch plan: timeline, owners, channels, KPI, and risk fallback.",
        ru: "Собери план запуска на 24 часа: таймлайн, владельцы, каналы, KPI и fallback по рискам.",
        reward: 6,
        feedbackEn: "Strong. This is execution-ready.",
        feedbackRu: "Сильно. Это уже готово к исполнению.",
      },
      {
        en: "Describe what launch means.",
        ru: "Опиши, что такое запуск.",
        reward: 2,
        feedbackEn: "Educational, but too passive for urgent work.",
        feedbackRu: "Образовательно, но слишком пассивно для срочной задачи.",
      },
    ],
  },
  {
    id: "challenge-3",
    promptEn: "You need better customer interviews. Select the prompt that increases signal quality.",
    promptRu: "Нужно улучшить интервью с клиентами. Выбери промпт, который повышает качество инсайтов.",
    choices: [
      {
        en: "Generate 5 generic questions.",
        ru: "Сгенерируй 5 общих вопросов.",
        reward: 2,
        feedbackEn: "A start, but not enough depth for reliable insight.",
        feedbackRu: "Неплохой старт, но мало глубины для надежных инсайтов.",
      },
      {
        en: "Create an interview script with hypotheses, probing questions, bias traps, and synthesis format.",
        ru: "Создай скрипт интервью: гипотезы, уточняющие вопросы, анти-байас ловушки и формат синтеза.",
        reward: 6,
        feedbackEn: "Excellent. This drives better decisions from each interview.",
        feedbackRu: "Отлично. Такой промпт делает каждое интервью полезнее для решений.",
      },
      {
        en: "Ask users if they like the product.",
        ru: "Спроси пользователей, нравится ли им продукт.",
        reward: 1,
        feedbackEn: "Weak signal. It won't reveal root causes.",
        feedbackRu: "Слабый сигнал. Корневые причины не вскроются.",
      },
    ],
  },
];
