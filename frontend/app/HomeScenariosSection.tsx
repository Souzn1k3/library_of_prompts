"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getTechniqueTranslationKey } from "@/lib/i18n";
import { SCENARIO_GAME_CHALLENGES } from "@/lib/scenarios/game";
import { buildScenarioOutputPreview } from "@/lib/scenarios/text";
import type { PromptListItem } from "@/lib/types";

type HomeScenariosSectionProps = {
  prompts: PromptListItem[];
  initialAuthenticated: boolean;
};

const TELEGRAM_BOT_URL = "https://t.me/prompts_souz_bot";

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

  const gameChallenge = SCENARIO_GAME_CHALLENGES[gameStep] ?? null;
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

    if (gameStep + 1 >= SCENARIO_GAME_CHALLENGES.length) {
      setGameStep(SCENARIO_GAME_CHALLENGES.length);
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
              {buildScenarioOutputPreview(language, scenario, scenarioInput)}
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
            {buildScenarioOutputPreview(language, activeScenario, scenarioInput)}
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
