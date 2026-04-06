"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getTechniqueTranslationKey, type Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type HomeScenariosSectionProps = {
  prompts: PromptListItem[];
  initialAuthenticated: boolean;
};

type GameChoice = {
  en: string;
  ru: string;
  reward: number;
  feedbackEn: string;
  feedbackRu: string;
};

type GameChallenge = {
  id: string;
  promptEn: string;
  promptRu: string;
  choices: GameChoice[];
};

const TELEGRAM_BOT_URL = "https://t.me/prompts_souz_bot";

const GAME_CHALLENGES: GameChallenge[] = [
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
    promptEn: "You need a launch plan in 24 hours. Choose the highest-leverage scenario.",
    promptRu: "Нужен план запуска за 24 часа. Выбери сценарий с максимальной пользой.",
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
    promptEn: "You need better customer interviews. Select the scenario that increases signal quality.",
    promptRu: "Нужно улучшить интервью с клиентами. Выбери сценарий, который повышает качество инсайтов.",
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
        feedbackRu: "Отлично. Такой сценарий делает каждое интервью полезнее для решений.",
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

export function HomeScenariosSection({ prompts, initialAuthenticated }: HomeScenariosSectionProps) {
  const { t, language } = useI18n();
  const scenarios = prompts.slice(0, 4);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(scenarios[0]?.id ?? null);
  const [scenarioInput, setScenarioInput] = useState("");
  const [gameStep, setGameStep] = useState(0);
  const [selectedChoiceIndex, setSelectedChoiceIndex] = useState<number | null>(null);
  const [gameTokens, setGameTokens] = useState(0);

  const activeScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === activeScenarioId) ?? scenarios[0] ?? null,
    [activeScenarioId, scenarios],
  );

  const gameChallenge = GAME_CHALLENGES[gameStep] ?? null;
  const selectedChoice = selectedChoiceIndex !== null && gameChallenge
    ? gameChallenge.choices[selectedChoiceIndex] ?? null
    : null;

  if (!scenarios.length) {
    return null;
  }

  function runNextGameStep() {
    if (!gameChallenge) {
      return;
    }

    if (selectedChoice) {
      setGameTokens((current) => current + selectedChoice.reward);
    }

    if (gameStep + 1 >= GAME_CHALLENGES.length) {
      setGameStep(GAME_CHALLENGES.length);
      setSelectedChoiceIndex(null);
      return;
    }

    setGameStep((current) => current + 1);
    setSelectedChoiceIndex(null);
  }

  function restartGame() {
    setGameStep(0);
    setSelectedChoiceIndex(null);
    setGameTokens(0);
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">{t("home.scenarioTryKicker")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("home.scenarioTryTitle")}</h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.scenarioTrySubtitle")}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {scenarios.map((scenario) => (
          <article key={`home-scenario-card-${scenario.id}`} className="pv-card p-4">
            <div className="flex items-start justify-between gap-2">
              <span className="pv-chip-brand">{t(getTechniqueTranslationKey(scenario.technique))}</span>
              {scenario.quality_score ? (
                <span className="pv-chip">{t("prompt.metricQuality", { count: scenario.quality_score })}</span>
              ) : null}
            </div>

            <h3 className="mt-3 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{scenario.title}</h3>
            <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-zinc-600">
              {scenario.summary ?? t("prompt.noSummary")}
            </p>

            <pre className="mt-3 line-clamp-4 rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
              {buildScenarioOutput(language, scenario, scenarioInput)}
            </pre>

            <div className="mt-3 flex flex-wrap gap-2">
              <Link href={`/prompt/${encodeURIComponent(scenario.slug)}`} className="pv-button-primary !w-auto">
                {t("home.scenarioCardOpen")}
              </Link>
              <button
                type="button"
                onClick={() => setActiveScenarioId(scenario.id)}
                className="pv-button-secondary !w-auto"
              >
                {t("home.scenarioCardTry")}
              </button>
            </div>
          </article>
        ))}
      </div>

      {activeScenario ? (
        <div className="mt-5 rounded-[1.1rem] border border-[var(--pv-border)] bg-white/80 p-4">
          <p className="text-sm font-semibold text-zinc-900">{t("home.scenarioLabTitle")}</p>
          <p className="mt-1 text-sm leading-relaxed text-zinc-600">{activeScenario.title}</p>
          <textarea
            value={scenarioInput}
            onChange={(event) => setScenarioInput(event.target.value)}
            className="pv-textarea mt-3 min-h-[86px]"
            placeholder={t("home.scenarioLabPlaceholder")}
          />
          <pre className="mt-3 max-h-[13rem] overflow-auto rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
            {buildScenarioOutput(language, activeScenario, scenarioInput)}
          </pre>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link href={`/prompt/${encodeURIComponent(activeScenario.slug)}`} className="pv-button-primary !w-auto">
              {t("home.scenarioCardOpen")}
            </Link>
            <Link href={initialAuthenticated ? "/dashboard" : "/signup"} className="pv-button-secondary !w-auto">
              {t(initialAuthenticated ? "home.entryNextActionSaveAuth" : "home.entryNextActionSaveGuest")}
            </Link>
          </div>
        </div>
      ) : null}

      <div className="mt-5 rounded-[1.2rem] border border-[var(--pv-border)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,248,255,0.9))] p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--pv-brand-strong)]">
              {t("home.gameKicker")}
            </p>
            <h3 className="mt-2 text-xl font-bold tracking-[-0.03em] text-zinc-950">{t("home.gameTitle")}</h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.gameSubtitle")}</p>
          </div>
          <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
            {t("home.gameTokensLabel", { count: gameTokens })}
          </span>
        </div>

        {gameChallenge ? (
          <div className="mt-4 space-y-3">
            <p className="text-sm font-semibold text-zinc-900">
              {language === "ru" ? gameChallenge.promptRu : gameChallenge.promptEn}
            </p>
            <div className="grid gap-2">
              {gameChallenge.choices.map((choice, index) => (
                <button
                  key={`${gameChallenge.id}-choice-${index}`}
                  type="button"
                  disabled={selectedChoiceIndex !== null}
                  onClick={() => setSelectedChoiceIndex(index)}
                  className={`rounded-[0.9rem] border p-3 text-left text-sm transition ${
                    selectedChoiceIndex === index
                      ? "border-[var(--pv-brand-strong)] bg-[var(--pv-brand-soft)] text-zinc-900"
                      : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300"
                  } disabled:cursor-not-allowed disabled:opacity-80`}
                >
                  {language === "ru" ? choice.ru : choice.en}
                </button>
              ))}
            </div>
            {selectedChoice ? (
              <div className="space-y-2 rounded-[0.9rem] border border-zinc-200 bg-white/80 p-3">
                <p className="text-sm text-zinc-700">
                  {language === "ru" ? selectedChoice.feedbackRu : selectedChoice.feedbackEn}
                </p>
                <p className="text-xs font-semibold text-emerald-700">
                  +{selectedChoice.reward} {t("home.gameTokenUnit")}
                </p>
                <button type="button" onClick={runNextGameStep} className="pv-button-primary !w-auto">
                  {t("home.gameNextStep")}
                </button>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="mt-4 space-y-3 rounded-[0.9rem] border border-emerald-200 bg-emerald-50/85 p-3">
            <p className="text-sm leading-relaxed text-emerald-900">{t("home.gameFinishedBody")}</p>
            <div className="flex flex-wrap gap-2">
              <a
                href={TELEGRAM_BOT_URL}
                target="_blank"
                rel="noreferrer"
                className="pv-button-primary !w-auto"
              >
                {t("home.gameOpenTelegram")}
              </a>
              <button type="button" onClick={restartGame} className="pv-button-secondary !w-auto">
                {t("home.gameRestart")}
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function buildScenarioOutput(language: Language, prompt: PromptListItem, userInput: string): string {
  const isRuFamily = language === "ru" || language === "tt";
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
