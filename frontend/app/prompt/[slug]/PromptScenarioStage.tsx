"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { buildScenarioLiveResult, isRuFamilyLanguage } from "@/features/scenarios/application/scenarioRuntime";
import { mapPromptToScenario } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import { useScenarioDemoRun } from "@/features/scenarios/presentation/useScenarioDemoRun";
import type { ScenarioResultDepth } from "@/features/scenarios/domain/scenario";
import { trackEvent } from "@/lib/analytics";
import type { Language } from "@/lib/i18n";
import type { PromptDetail } from "@/lib/types";

type PromptScenarioStageProps = {
  language: Language;
  prompt: PromptDetail;
};

export function PromptScenarioStage({ language, prompt }: PromptScenarioStageProps) {
  const [scenarioInput, setScenarioInput] = useState("");
  const [committedInput, setCommittedInput] = useState("");
  const [outputMode, setOutputMode] = useState<ScenarioResultDepth>("detailed");
  const [refreshSeed, setRefreshSeed] = useState(0);

  const bodyLocked = Boolean(prompt.body_locked);
  const localized = getLocalizedCopy(language);
  const scenarioDefinition = useMemo(() => mapPromptToScenario(prompt), [prompt]);
  const demoRun = useScenarioDemoRun(prompt.slug);
  const runGuardMessage = formatRunGuardMessage(demoRun.latestMessage, localized);

  const liveResult = useMemo(
    () =>
      buildScenarioLiveResult({
        language,
        scenario: scenarioDefinition,
        taskInput: committedInput,
        outputDepth: outputMode,
        variationSeed: refreshSeed,
      }),
    [committedInput, language, outputMode, refreshSeed, scenarioDefinition],
  );

  useEffect(() => {
    if (!bodyLocked) {
      return;
    }
    trackEvent({
      eventName: "paywall_viewed",
      page: `/prompt/${prompt.slug}`,
      feature: "scenario_stage_lock",
      onceKey: `paywall_viewed:prompt:${prompt.slug}`,
      metadata: {
        prompt_slug: prompt.slug,
        surface: "scenario_stage",
      },
    });
  }, [bodyLocked, prompt.slug]);

  async function runScenarioNow() {
    const run = await demoRun.run(scenarioInput.trim() ? scenarioInput : null);
    if (!run?.executed) {
      return;
    }
    setCommittedInput(scenarioInput);
    setRefreshSeed((current) => current + 1);
    trackEvent({
      eventName: "scenario_run",
      page: `/prompt/${prompt.slug}`,
      feature: "prompt_scenario_stage",
      metadata: { prompt_slug: prompt.slug },
    });
  }

  function refreshLocalPreview() {
    setCommittedInput(scenarioInput);
    setRefreshSeed((current) => current + 1);
  }

  async function purchaseBoost() {
    const purchase = await demoRun.purchaseBoost();
    if (!purchase) {
      return;
    }
    trackEvent({
      eventName: "scenario_upgrade_clicked",
      page: `/prompt/${prompt.slug}`,
      feature: "prompt_scenario_stage",
      metadata: {
        prompt_slug: prompt.slug,
        source: "token_boost",
        applied_bonus_runs: purchase.applied_bonus_runs,
      },
    });
  }

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
                  className={`pv-segment-pill ${outputMode === "detailed" ? "pv-segment-pill-active" : ""}`}
                >
                  {localized.modeDetailed}
                </button>
                <button
                  type="button"
                  onClick={() => setOutputMode("concise")}
                  className={`pv-segment-pill ${outputMode === "concise" ? "pv-segment-pill-active" : ""}`}
                >
                  {localized.modeConcise}
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={() => void runScenarioNow()}
              className="pv-button-primary !w-auto"
              disabled={demoRun.runPending || demoRun.capReached}
            >
              {demoRun.runPending ? localized.runPending : localized.runNow}
            </button>
            <button
              type="button"
              onClick={refreshLocalPreview}
              className="pv-button-secondary !w-auto"
              disabled={!scenarioInput.trim()}
            >
              {localized.refreshResult}
            </button>

            {!demoRun.isPro ? (
              <p className="text-xs text-zinc-500">
                {localized.demoRunsLeft.replace("{count}", String(demoRun.remainingRuns ?? 0))}
              </p>
            ) : (
              <p className="text-xs text-emerald-700">{localized.demoUnlimited}</p>
            )}
            {demoRun.capReached ? <p className="text-xs text-amber-700">{localized.demoCapReached}</p> : null}
            {!demoRun.isPro ? (
              <p className="text-xs text-emerald-700">
                {localized.bonusRunsLeft.replace("{count}", String(demoRun.bonusRunsRemaining ?? 0))}
              </p>
            ) : null}
            {!demoRun.isPro ? (
              <button
                type="button"
                onClick={() => void purchaseBoost()}
                className="pv-button-secondary !w-auto"
                disabled={demoRun.boostPending}
              >
                {demoRun.boostPending ? localized.boostPending : localized.boostAction}
              </button>
            ) : null}
            {runGuardMessage ? <p className="text-xs text-zinc-500">{runGuardMessage}</p> : null}
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
                <Link
                  href="/pricing?tier=starter"
                  className="pv-button-primary !w-auto"
                  onClick={() => {
                    trackEvent({
                      eventName: "paywall_interaction",
                      page: `/prompt/${prompt.slug}`,
                      feature: "scenario_stage_lock",
                      metadata: {
                        prompt_slug: prompt.slug,
                        action: "unlock_click",
                      },
                    });
                    trackEvent({
                      eventName: "upgrade_clicked",
                      page: `/prompt/${prompt.slug}`,
                      feature: "scenario_stage_lock",
                      metadata: {
                        prompt_slug: prompt.slug,
                        source: "prompt_scenario_stage",
                      },
                    });
                  }}
                >
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
      runNow: "Запустить сценарий",
      runPending: "Запуск...",
      demoRunsLeft: "Осталось демо-запусков: {count}",
      demoUnlimited: "PRO: лимитов на запуски нет",
      bonusRunsLeft: "Бонусных запусков осталось: {count}",
      boostAction: "Купить +3 запуска за Tokens",
      boostPending: "Покупка...",
      boostAdded: "Бонусные запуски добавлены: +{count}.",
      boostFailed: "Не удалось купить бонусные запуски.",
      demoCapReached: "Лимит демо-запусков достигнут. Перейдите на PRO.",
      demoIpCapReached: "Достигнут дневной лимит гостевых запусков для этого сценария.",
      demoFingerprintCapReached: "Достигнут дневной лимит по отпечатку устройства для этого сценария.",
      demoRotationCapReached: "Слишком много гостевых сессий в этой сети. Войдите в аккаунт.",
      runUnavailable: "Запуск временно недоступен. Попробуйте снова.",
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
    runNow: "Run scenario",
    runPending: "Running...",
    demoRunsLeft: "Demo runs left: {count}",
    demoUnlimited: "PRO: unlimited runs",
    bonusRunsLeft: "Bonus runs left: {count}",
    boostAction: "Buy +3 runs with Tokens",
    boostPending: "Purchasing...",
    boostAdded: "Bonus runs added: +{count}.",
    boostFailed: "Could not purchase bonus runs.",
    demoCapReached: "Demo run cap reached. Upgrade to PRO.",
    demoIpCapReached: "Guest daily run limit reached for this scenario.",
    demoFingerprintCapReached: "Guest fingerprint daily run limit reached for this scenario.",
    demoRotationCapReached: "Too many guest sessions detected on this network. Please sign in.",
    runUnavailable: "Run is temporarily unavailable. Please try again.",
  };
}

function formatRunGuardMessage(
  reason: string | null,
  localized: ReturnType<typeof getLocalizedCopy>,
): string | null {
  if (!reason) {
    return null;
  }
  if (reason === "free_demo_cap_reached") {
    return localized.demoCapReached;
  }
  if (reason === "guest_ip_prompt_daily_cap_reached") {
    return localized.demoIpCapReached;
  }
  if (reason === "guest_fingerprint_prompt_daily_cap_reached") {
    return localized.demoFingerprintCapReached;
  }
  if (reason === "guest_ip_rotation_detected") {
    return localized.demoRotationCapReached;
  }
  if (reason === "run_unavailable") {
    return localized.runUnavailable;
  }
  if (reason.startsWith("bonus_runs_added:")) {
    const count = Number(reason.split(":")[1] ?? "0");
    return localized.boostAdded.replace("{count}", String(count));
  }
  if (reason === "boost_purchase_failed") {
    return localized.boostFailed;
  }
  if (reason === "pro_unlimited_runs") {
    return localized.demoUnlimited;
  }
  return reason;
}
