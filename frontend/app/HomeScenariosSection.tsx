"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { buildScenarioLiveResult } from "@/features/scenarios/application/scenarioRuntime";
import { mapPromptListToScenarios } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import { useScenarioGameLedger } from "@/features/scenarios/presentation/useScenarioGameLedger";
import { trackEvent } from "@/lib/analytics";
import { SCENARIO_GAME_CHALLENGES } from "@/lib/scenarios/game";
import type {
  PromptListItem,
  ScenarioChainRead,
  ScenarioNextStepRead,
  ScenarioPackRead,
  ScenarioPricingPlanRead,
  ScenarioReturnTriggerRead,
  ScenarioShowcaseRead,
} from "@/lib/types";

type HomeScenariosSectionProps = {
  prompts: PromptListItem[];
  recommendedPrompts: PromptListItem[];
  retentionPrompts: PromptListItem[];
  packs: ScenarioPackRead[];
  chains: ScenarioChainRead[];
  nextSteps: ScenarioNextStepRead[];
  returnTriggers: ScenarioReturnTriggerRead[];
  showcase: ScenarioShowcaseRead[];
  pricingPlans: ScenarioPricingPlanRead[];
  initialAuthenticated: boolean;
};

const TELEGRAM_BOT_URL = "https://t.me/prompts_souz_bot";

export function HomeScenariosSection({
  prompts,
  recommendedPrompts,
  retentionPrompts,
  packs,
  chains,
  nextSteps,
  returnTriggers,
  showcase,
  pricingPlans,
  initialAuthenticated,
}: HomeScenariosSectionProps) {
  const { t, language } = useI18n();

  const featuredScenarios = useMemo(
    () => mapPromptListToScenarios(dedupePrompts([...recommendedPrompts, ...prompts]).slice(0, 4)),
    [prompts, recommendedPrompts],
  );

  const chainScenarios = useMemo(
    () => mapPromptListToScenarios(dedupePrompts([...retentionPrompts, ...prompts]).slice(0, 3)),
    [prompts, retentionPrompts],
  );
  const chainSteps = useMemo(
    () => chains.find((chain) => chain.steps.length >= 2)?.steps ?? [],
    [chains],
  );

  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(featuredScenarios[0]?.id ?? null);
  const [scenarioInput, setScenarioInput] = useState("");
  const [gameStep, setGameStep] = useState(0);
  const [selectedChoiceIndex, setSelectedChoiceIndex] = useState<number | null>(null);
  const [previewTokens, setPreviewTokens] = useState(0);
  const gameLedger = useScenarioGameLedger();

  const activeScenario = useMemo(
    () => featuredScenarios.find((scenario) => scenario.id === activeScenarioId) ?? featuredScenarios[0] ?? null,
    [activeScenarioId, featuredScenarios],
  );

  const gameChallenge = SCENARIO_GAME_CHALLENGES[gameStep] ?? null;
  const selectedChoice =
    selectedChoiceIndex !== null && gameChallenge ? gameChallenge.choices[selectedChoiceIndex] ?? null : null;

  const totalSaveSignals = featuredScenarios.reduce((acc, scenario) => acc + scenario.saveCount, 0);
  const highQualityScenarios = featuredScenarios.filter((scenario) => scenario.qualityScore >= 70).length;

  if (!featuredScenarios.length) {
    return null;
  }

  async function runNextGameStep() {
    if (!gameChallenge) {
      return;
    }

    if (selectedChoice && selectedChoiceIndex !== null) {
      setPreviewTokens((current) => current + selectedChoice.reward);
      await gameLedger.earn(gameChallenge.id, selectedChoiceIndex);
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
    setPreviewTokens(0);
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
        {featuredScenarios.map((scenario) => (
          <article key={`home-scenario-card-${scenario.id}`} className="pv-card p-4">
            <div className="flex items-start justify-between gap-2">
              <span className="pv-chip-brand">{scenario.category}</span>
              {scenario.qualityScore > 0 ? (
                <span className="pv-chip">{t("prompt.metricQuality", { count: scenario.qualityScore })}</span>
              ) : null}
            </div>

            <h3 className="mt-3 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{scenario.title}</h3>
            <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-zinc-600">{scenario.summary}</p>

            <pre className="mt-3 line-clamp-4 rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
              {buildScenarioLiveResult({
                language,
                scenario,
                taskInput: scenarioInput,
                outputDepth: "concise",
              })}
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
            {buildScenarioLiveResult({
              language,
              scenario: activeScenario,
              taskInput: scenarioInput,
              outputDepth: "detailed",
            })}
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

      {packs.length ? (
        <div className="mt-5 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.packKicker")}</p>
          <div className="grid gap-3 lg:grid-cols-3">
            {packs.slice(0, 3).map((pack) => (
              <article key={`home-pack-${pack.id}`} className="rounded-[1rem] border border-zinc-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{pack.id}</p>
                <h3 className="mt-2 text-base font-semibold text-zinc-950">{pack.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{pack.description}</p>
                <p className="mt-2 text-xs text-emerald-700">{pack.outcome}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {pack.prompts.slice(0, 3).map((prompt) => (
                    <span key={`${pack.id}-${prompt.id}`} className="rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] text-zinc-600">
                      {prompt.title}
                    </span>
                  ))}
                </div>
                <Link
                  href={`/prompt/${encodeURIComponent(pack.cta_prompt_slug ?? pack.prompt_slugs[0] ?? "")}`}
                  className="pv-inline-link mt-3 text-sm"
                  onClick={() =>
                    trackEvent({
                      eventName: "scenario_pack_started",
                      page: "/",
                      feature: "home_packs",
                      metadata: { pack_id: pack.id, prompt_slug: pack.cta_prompt_slug ?? null },
                    })}
                >
                  {t("home.packAction")}
                  <span aria-hidden="true">↗</span>
                </Link>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <article className="rounded-[1.1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.scenarioChainKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.scenarioChainTitle")}</h3>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.scenarioChainSubtitle")}</p>
          <div className="mt-3 space-y-2">
            {(chainSteps.length
              ? chainSteps.map((step) => ({
                key: step.prompt_slug,
                title: step.title,
                summary: step.goal,
              }))
              : chainScenarios.map((scenario) => ({
                key: scenario.id,
                title: scenario.title,
                summary: scenario.summary,
              }))
            ).map((item, index) => (
              <div key={`home-chain-${item.key}`} className="rounded-[0.9rem] border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">
                  {t("home.scenarioChainStep", { count: index + 1 })}
                </p>
                <p className="mt-1 text-sm font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{item.summary}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[1.1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.retentionKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.retentionTitle")}</h3>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.retentionSubtitle")}</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <div className="rounded-[0.9rem] border border-zinc-200 bg-white p-3">
              <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("home.retentionMetricScenarios")}</p>
              <p className="mt-1 text-xl font-semibold tracking-[-0.03em] text-zinc-950">{featuredScenarios.length}</p>
            </div>
            <div className="rounded-[0.9rem] border border-zinc-200 bg-white p-3">
              <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("home.retentionMetricSaves")}</p>
              <p className="mt-1 text-xl font-semibold tracking-[-0.03em] text-zinc-950">{totalSaveSignals}</p>
            </div>
            <div className="rounded-[0.9rem] border border-zinc-200 bg-white p-3">
              <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("home.retentionMetricQuality")}</p>
              <p className="mt-1 text-xl font-semibold tracking-[-0.03em] text-zinc-950">{highQualityScenarios}</p>
            </div>
            <div className="rounded-[0.9rem] border border-zinc-200 bg-white p-3">
              <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{t("home.gameTokenUnit")}</p>
              <p className="mt-1 text-xl font-semibold tracking-[-0.03em] text-zinc-950">
                {gameLedger.gameState?.pending_tokens ?? 0}
              </p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link href={initialAuthenticated ? "/dashboard" : "/signup"} className="pv-button-secondary !w-auto">
              {t(initialAuthenticated ? "home.retentionWorkspaceAuth" : "home.retentionWorkspaceGuest")}
            </Link>
            <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">
              {t("home.retentionUpgrade")}
            </Link>
          </div>
        </article>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <article className="rounded-[1.1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.nextStepKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.nextStepTitle")}</h3>
          <div className="mt-3 space-y-2">
            {nextSteps.slice(0, 3).map((step) => (
              <Link
                key={`next-step-${step.next_prompt_slug}`}
                href={`/prompt/${encodeURIComponent(step.next_prompt_slug)}`}
                className="block rounded-[0.9rem] border border-zinc-200 bg-white p-3"
                onClick={() =>
                  trackEvent({
                    eventName: "scenario_chain_next_clicked",
                    page: "/",
                    feature: "home_next_steps",
                    metadata: {
                      source_prompt_slug: step.source_prompt_slug,
                      next_prompt_slug: step.next_prompt_slug,
                    },
                  })}
              >
                <p className="text-xs font-semibold text-zinc-800">{step.next_prompt_slug}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{step.reason}</p>
              </Link>
            ))}
            {!nextSteps.length ? <p className="text-sm text-zinc-600">{t("home.nextStepEmpty")}</p> : null}
          </div>
        </article>

        <article className="rounded-[1.1rem] border border-[var(--pv-border)] bg-zinc-50/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.returnKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.returnTitle")}</h3>
          <div className="mt-3 space-y-2">
            {returnTriggers.slice(0, 3).map((trigger) => (
              <Link key={trigger.trigger_key} href={trigger.href} className="block rounded-[0.9rem] border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold text-zinc-900">{trigger.label}</p>
                <p className="mt-1 text-xs text-zinc-600">{t("home.returnCount", { count: trigger.count })}</p>
              </Link>
            ))}
            {!returnTriggers.length ? <p className="text-sm text-zinc-600">{t("home.returnEmpty")}</p> : null}
          </div>
        </article>
      </div>

      {showcase.length ? (
        <div className="mt-5 rounded-[1.2rem] border border-[var(--pv-border)] bg-white/85 p-4 sm:p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.showcaseKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.showcaseTitle")}</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            {showcase.slice(0, 3).map((item) => (
              <article key={item.share_id} className="rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-semibold text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{item.excerpt}</p>
                <pre className="mt-2 max-h-[6rem] overflow-auto rounded-[0.7rem] border border-zinc-200 bg-white p-2 text-[11px] leading-relaxed text-zinc-700 whitespace-pre-wrap">
                  {item.output_preview}
                </pre>
              </article>
            ))}
          </div>
        </div>
      ) : null}

      {pricingPlans.length ? (
        <div className="mt-5 rounded-[1.2rem] border border-[var(--pv-border)] bg-white/85 p-4 sm:p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">{t("home.pricingKicker")}</p>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{t("home.pricingTitle")}</h3>
          <div className="mt-3 grid gap-3 md:grid-cols-4">
            {pricingPlans.map((plan) => (
              <article key={plan.tier} className="rounded-[0.9rem] border border-zinc-200 bg-zinc-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{plan.tier}</p>
                <p className="mt-1 text-lg font-semibold text-zinc-950">${plan.price_monthly_usd}</p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-600">{plan.headline}</p>
              </article>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link href="/studio" className="pv-button-secondary !w-auto">
              {t("home.pricingStudioAction")}
            </Link>
            <Link href="/scenarios/marketplace" className="pv-button-primary !w-auto">
              {t("home.pricingMarketplaceAction")}
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
            {t("home.gameTokensLabel", { count: gameLedger.gameState?.pending_tokens ?? 0 })}
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
                <p className="text-sm text-zinc-700">{language === "ru" ? selectedChoice.feedbackRu : selectedChoice.feedbackEn}</p>
                <p className="text-xs font-semibold text-emerald-700">
                  +{selectedChoice.reward} {t("home.gameTokenUnit")}
                </p>
                <button type="button" onClick={() => void runNextGameStep()} className="pv-button-primary !w-auto" disabled={gameLedger.earnPending}>
                  {t("home.gameNextStep")}
                </button>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="mt-4 space-y-3 rounded-[0.9rem] border border-emerald-200 bg-emerald-50/85 p-3">
            <p className="text-sm leading-relaxed text-emerald-900">{t("home.gameFinishedBody")}</p>
            <p className="text-xs leading-relaxed text-emerald-800">{t("home.gameTokenSpendHint")}</p>
            <p className="text-xs leading-relaxed text-zinc-700">
              {t("home.gamePendingServer", {
                pending: gameLedger.gameState?.pending_tokens ?? 0,
                preview: previewTokens,
              })}
            </p>
            {gameLedger.latestMessage ? <p className="text-xs text-zinc-700">{gameLedger.latestMessage}</p> : null}
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void gameLedger.claim()}
                className="pv-button-primary !w-auto"
                disabled={gameLedger.claimPending}
              >
                {gameLedger.claimPending ? t("home.gameClaimPending") : t("home.gameClaimAction")}
              </button>
              <a href={TELEGRAM_BOT_URL} target="_blank" rel="noreferrer" className="pv-button-primary !w-auto">
                {t("home.gameOpenTelegram")}
              </a>
              <Link href="/store" className="pv-button-secondary !w-auto">
                {t("home.gameTokenSpendAction")}
              </Link>
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

function dedupePrompts(prompts: PromptListItem[]): PromptListItem[] {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}
