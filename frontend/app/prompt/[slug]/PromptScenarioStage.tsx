"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { buildScenarioLiveResult, isRuFamilyLanguage } from "@/features/scenarios/application/scenarioRuntime";
import { mapPromptToScenario } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import type { ScenarioResultDepth } from "@/features/scenarios/domain/scenario";
import type { Language } from "@/lib/i18n";
import type { PromptDetail } from "@/lib/types";

type PromptScenarioStageProps = {
  language: Language;
  prompt: PromptDetail;
};

export function PromptScenarioStage({ language, prompt }: PromptScenarioStageProps) {
  const [scenarioInput, setScenarioInput] = useState("");
  const [outputMode, setOutputMode] = useState<ScenarioResultDepth>("detailed");
  const [refreshSeed, setRefreshSeed] = useState(0);

  const bodyLocked = Boolean(prompt.body_locked);
  const localized = getLocalizedCopy(language);
  const scenarioDefinition = useMemo(() => mapPromptToScenario(prompt), [prompt]);

  const liveResult = useMemo(
    () =>
      buildScenarioLiveResult({
        language,
        scenario: scenarioDefinition,
        taskInput: scenarioInput,
        outputDepth: outputMode,
        variationSeed: refreshSeed,
      }),
    [language, outputMode, refreshSeed, scenarioDefinition, scenarioInput],
  );

  return (
    <section className="pv-panel overflow-hidden p-0">
      <div className="grid min-h-[80vh] lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
        <div className="relative flex flex-col bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(30,41,59,0.94))] px-6 py-6 text-white sm:px-8 sm:py-8">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(59,130,246,0.35),transparent_40%),radial-gradient(circle_at_90%_90%,rgba(16,185,129,0.24),transparent_35%)]" />
          <div className="relative z-10 flex h-full flex-col">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-200">
              {localized.liveResultKicker}
            </p>
            <h1 className="mt-3 max-w-[20ch] text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">
              {prompt.title}
            </h1>
            <p className="mt-3 max-w-[42rem] text-sm leading-relaxed text-slate-200">
              {localized.liveResultSubtitle}
            </p>

            <pre className="mt-5 min-h-[18rem] flex-1 overflow-auto rounded-[1.1rem] border border-white/15 bg-black/25 p-4 text-sm leading-relaxed text-slate-100 whitespace-pre-wrap shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
              {liveResult}
            </pre>
          </div>
        </div>

        <aside className="flex flex-col justify-between gap-4 bg-white/90 px-6 py-6 sm:px-7 sm:py-7">
          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                {localized.controlKicker}
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-zinc-950">
                {localized.controlTitle}
              </h2>
            </div>

            <textarea
              value={scenarioInput}
              onChange={(event) => setScenarioInput(event.target.value)}
              className="pv-textarea min-h-[120px]"
              placeholder={localized.inputPlaceholder}
            />

            <div className="space-y-2">
              <p className="pv-label">{localized.modeLabel}</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setOutputMode("detailed")}
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    outputMode === "detailed"
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                  }`}
                >
                  {localized.modeDetailed}
                </button>
                <button
                  type="button"
                  onClick={() => setOutputMode("concise")}
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    outputMode === "concise"
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                  }`}
                >
                  {localized.modeConcise}
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setRefreshSeed((current) => current + 1)}
              className="pv-button-secondary !w-auto"
            >
              {localized.refreshResult}
            </button>
          </div>

          <div className="space-y-3 rounded-[1rem] border border-[var(--pv-border)] bg-white/85 p-4">
            <p className="text-sm font-semibold text-zinc-950">
              {bodyLocked ? localized.lockedTitle : localized.unlockedTitle}
            </p>
            <p className="text-sm leading-relaxed text-zinc-600">
              {bodyLocked ? localized.lockedBody : localized.unlockedBody}
            </p>
            {bodyLocked ? (
              <div className="flex flex-wrap gap-2">
                <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">
                  {localized.unlockCta}
                </Link>
                <a
                  href="https://t.me/prompts_souz_bot"
                  target="_blank"
                  rel="noreferrer"
                  className="pv-button-secondary !w-auto"
                >
                  {localized.telegramCta}
                </a>
              </div>
            ) : (
              <a
                href="https://t.me/prompts_souz_bot"
                target="_blank"
                rel="noreferrer"
                className="pv-button-secondary !w-auto"
              >
                {localized.telegramCta}
              </a>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}

function getLocalizedCopy(language: Language) {
  if (isRuFamilyLanguage(language)) {
    return {
      liveResultKicker: "Живой результат сценария",
      liveResultSubtitle: "Сначала вы видите итог AI-работы. Ниже — полный сценарий и доступ к его логике.",
      controlKicker: "Сценарий в действии",
      controlTitle: "Попробуйте на своей задаче",
      inputPlaceholder: "Опишите вашу задачу в 1-2 предложениях, чтобы адаптировать результат.",
      modeLabel: "Глубина результата",
      modeDetailed: "Подробно",
      modeConcise: "Кратко",
      refreshResult: "Обновить результат",
      lockedTitle: "Полный сценарий закрыт",
      lockedBody: "Free-пользователь видит результат и демо. PRO открывает полный blueprint, копирование и кастомизацию.",
      unlockCta: "Разблокировать сценарий (PRO)",
      telegramCta: "Продолжить в Telegram-боте",
      unlockedTitle: "Полный сценарий доступен",
      unlockedBody: "Вы можете копировать и адаптировать сценарий под свои данные прямо сейчас.",
    };
  }

  return {
    liveResultKicker: "Live scenario output",
    liveResultSubtitle: "You see the AI result first. The full scenario logic is available below.",
    controlKicker: "Scenario in action",
    controlTitle: "Try it on your task",
    inputPlaceholder: "Describe your task in 1-2 sentences to adapt the output.",
    modeLabel: "Output depth",
    modeDetailed: "Detailed",
    modeConcise: "Concise",
    refreshResult: "Refresh output",
    lockedTitle: "Full scenario is locked",
    lockedBody: "Free users get result preview and demo. PRO unlocks full blueprint, copying, and customization.",
    unlockCta: "Unlock scenario (PRO)",
    telegramCta: "Continue in Telegram bot",
    unlockedTitle: "Full scenario is available",
    unlockedBody: "You can copy and customize this scenario right now.",
  };
}
