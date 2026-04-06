"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { fetchScenarioMarketplace } from "@/lib/client-api";

import styles from "./ScenarioRuntimeRoot.module.css";
import { InteractionController } from "./InteractionController";
import { ScenarioRuntimeEngine } from "./ScenarioRuntimeEngine";
import { ScenarioStateStore } from "./ScenarioStateStore";
import type { ScenarioRuntimeFeedback } from "./types";
import { useStore } from "zustand";

const ScenarioRuntimeCanvas = dynamic(
  () => import("./ScenarioRuntimeCanvas").then((module) => module.ScenarioRuntimeCanvas),
  {
    ssr: false,
    loading: () => <div className="h-full w-full bg-slate-950/60" />,
  },
);

function feedbackClass(tone: ScenarioRuntimeFeedback["tone"]): string {
  if (tone === "positive") {
    return styles.feedbackPositive;
  }
  if (tone === "warning") {
    return styles.feedbackWarning;
  }
  return "";
}

export function ScenarioRuntimeRoot() {
  const [stateStore] = useState(() => new ScenarioStateStore());
  const [engine] = useState(() => new ScenarioRuntimeEngine(stateStore));
  const [controller] = useState(() => new InteractionController(engine));

  const stage = useStore(stateStore.api, (state) => state.stage);
  const runtimeMode = useStore(stateStore.api, (state) => state.runtimeMode);
  const tier = useStore(stateStore.api, (state) => state.tier);
  const scenarios = useStore(stateStore.api, (state) => state.scenarios);
  const activeScenarioId = useStore(stateStore.api, (state) => state.activeScenarioId);
  const result = useStore(stateStore.api, (state) => state.result);
  const metrics = useStore(stateStore.api, (state) => state.metrics);
  const traces = useStore(stateStore.api, (state) => state.traces);
  const feedback = useStore(stateStore.api, (state) => state.feedback);
  const pro = useStore(stateStore.api, (state) => state.pro);
  const tool = useStore(stateStore.api, (state) => state.tool);
  const ai = useStore(stateStore.api, (state) => state.ai);

  const activeScenario = scenarios.find((item) => item.id === activeScenarioId) ?? scenarios[0];

  useEffect(() => {
    engine.start();
    return () => {
      engine.stop();
    };
  }, [engine]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      if (tagName === "input" || tagName === "textarea" || target?.isContentEditable) {
        return;
      }
      controller.keyboard(event.key);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [controller]);

  useEffect(() => {
    let cancelled = false;

    void fetchScenarioMarketplace({ limit: 9, section: "trending" })
      .then((rows) => {
        if (cancelled || !rows.length) {
          return;
        }
        engine.hydrateMarketplaceScenarios(rows);
      })
      .catch(() => {
        // Keep local fallback scenarios when API is unavailable.
      });

    return () => {
      cancelled = true;
    };
  }, [engine]);

  return (
    <section className={styles.root} aria-label="ScenarioRuntimeRoot" data-runtime-mode={runtimeMode}>
      <header className={styles.topbar}>
        <div className="min-w-0 space-y-2">
          <div className={styles.brand}>
            <span className={styles.dot} aria-hidden="true" />
            <span>Scenario Runtime Root</span>
          </div>
          <div className={styles.scenarioRail}>
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                type="button"
                className={`${styles.scenarioButton} ${scenario.id === activeScenarioId ? styles.scenarioButtonActive : ""}`}
                onClick={() => controller.setScenario(scenario.id)}
                title={`${scenario.title} (${scenario.category})`}
              >
                {scenario.title}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.topControls}>
          <span className={styles.actionButton}>{runtimeMode.toUpperCase()} MODE</span>
          <button
            type="button"
            className={styles.tierButton}
            data-active={tier === "free"}
            onClick={() => controller.setTier("free")}
          >
            Free
          </button>
          <button
            type="button"
            className={styles.tierButton}
            data-active={tier === "pro"}
            onClick={() => controller.setTier("pro")}
          >
            Pro
          </button>
          <button type="button" className={styles.actionButton} onClick={() => controller.toggleProPanel()}>
            {pro.panelOpen ? "Hide Layer" : "Pro Layer"}
          </button>
        </div>
      </header>

      <div className={styles.core}>
        <div className={styles.stage}>
          <ScenarioRuntimeCanvas
            engine={engine}
            controller={controller}
            stageWidth={stage.width}
            stageHeight={stage.height}
            className={styles.canvas}
          />

          <div className={styles.stageOverlayTop}>
            <p className={styles.headline}>{result.headline}</p>
            <p className={styles.summary}>{result.summary}</p>
            <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-cyan-100/80">
              {activeScenario?.title ?? "Runtime Scenario"} · {activeScenario?.category ?? "custom"}
            </p>
          </div>

          <div className={styles.stageOverlayBottom}>
            {result.cards.map((card) => (
              <article key={card.id} className={styles.resultCard}>
                <p className={styles.resultLabel}>{card.label}</p>
                <p
                  className={`${styles.resultValue} ${card.tone === "positive" ? styles.tonePositive : card.tone === "warning" ? styles.toneWarning : styles.toneNeutral}`}
                >
                  {card.value}
                </p>
              </article>
            ))}
          </div>
        </div>

        <aside className={styles.sidebar}>
          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>Runtime Metrics</h2>
            <div className={styles.metricGrid}>
              <article className={styles.metricItem}>
                <p className={styles.metricLabel}>FPS</p>
                <p className={styles.metricValue}>{metrics.fps}</p>
              </article>
              <article className={styles.metricItem}>
                <p className={styles.metricLabel}>Reaction</p>
                <p className={styles.metricValue}>{metrics.reactionMs} ms</p>
              </article>
              <article className={styles.metricItem}>
                <p className={styles.metricLabel}>Actions</p>
                <p className={styles.metricValue}>{metrics.interactions}</p>
              </article>
              <article className={styles.metricItem}>
                <p className={styles.metricLabel}>Loops</p>
                <p className={styles.metricValue}>{metrics.loops}</p>
              </article>
            </div>

            <div className={styles.controlStack}>
              <button type="button" className={styles.actionButton} onClick={() => controller.pulse()}>
                Pulse Stage
              </button>
              <button type="button" className={styles.actionButton} onClick={() => controller.generate()}>
                Regenerate Stream
              </button>
            </div>
          </section>

          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>Live Stream</h2>
            <div className={styles.streamList}>
              {result.stream.length ? (
                result.stream.map((line, index) => (
                  <p key={`${line}-${index}`} className={styles.streamItem}>
                    {line}
                  </p>
                ))
              ) : (
                <p className={styles.streamItem}>stream waiting for interaction</p>
              )}
            </div>
            <p className="mt-2 text-xs text-cyan-100/70">{result.streaming ? "Streaming..." : "Stream synced"}</p>
          </section>

          <section className={styles.panel}>
            <h2 className={styles.panelTitle}>Interaction Trace</h2>
            <div className={styles.traceList}>
              {traces.slice(0, 8).map((trace) => (
                <p key={trace.id} className={styles.traceItem}>
                  [{trace.signal}] {trace.detail}
                </p>
              ))}
            </div>
            <p className={`${styles.feedback} ${feedbackClass(feedback.tone)}`}>
              <strong>{feedback.title}</strong>
              <br />
              {feedback.detail}
            </p>
          </section>
        </aside>
      </div>

      <section className={`${styles.bottomLayer} ${pro.panelOpen ? styles.bottomLayerOpen : ""}`}>
        <div className={styles.bottomGrid}>
          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>Input Control</h3>
            <div className={styles.controlStack}>
              <label className={styles.inlineControl} htmlFor="runtime-objective">
                Objective
              </label>
              <input
                id="runtime-objective"
                className={styles.input}
                value={ai.objective}
                onChange={(event) => controller.setObjective(event.target.value)}
                placeholder="Set runtime objective"
              />

              <label className={styles.inlineControl} htmlFor="runtime-temperature">
                <span>Temperature</span>
                <span>{ai.temperature.toFixed(2)}</span>
              </label>
              <input
                id="runtime-temperature"
                type="range"
                className={styles.range}
                min={0.05}
                max={1}
                step={0.01}
                value={ai.temperature}
                onChange={(event) => controller.setTemperature(Number(event.target.value))}
              />
            </div>
          </article>

          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>Tool Levers</h3>
            <div className={styles.controlStack}>
              <label className={styles.inlineControl} htmlFor="runtime-intensity">
                <span>Intensity</span>
                <span>{tool.intensity}%</span>
              </label>
              <input
                id="runtime-intensity"
                type="range"
                className={styles.range}
                min={0}
                max={100}
                step={1}
                value={tool.intensity}
                onChange={(event) => controller.setIntensity(Number(event.target.value))}
              />

              <label className={styles.inlineControl} htmlFor="runtime-precision">
                <span>Precision</span>
                <span>{tool.precision}%</span>
              </label>
              <input
                id="runtime-precision"
                type="range"
                className={styles.range}
                min={0}
                max={100}
                step={1}
                value={tool.precision}
                onChange={(event) => controller.setPrecision(Number(event.target.value))}
              />

              <label className={styles.inlineControl} htmlFor="runtime-automation">
                <span>Automation</span>
                <span>{tool.automation}%</span>
              </label>
              <input
                id="runtime-automation"
                type="range"
                className={styles.range}
                min={0}
                max={100}
                step={1}
                value={tool.automation}
                onChange={(event) => controller.setAutomation(Number(event.target.value))}
              />
            </div>
          </article>

          <article className={styles.panel}>
            <h3 className={styles.panelTitle}>Pro Graph</h3>
            {tier === "pro" ? (
              <div className={styles.controlStack}>
                <label className={styles.inlineControl} htmlFor="runtime-graph-depth">
                  <span>Graph depth</span>
                  <span>{pro.graphDepth}</span>
                </label>
                <input
                  id="runtime-graph-depth"
                  type="range"
                  className={styles.range}
                  min={1}
                  max={6}
                  step={1}
                  value={pro.graphDepth}
                  onChange={(event) => controller.setGraphDepth(Number(event.target.value))}
                />
                <button type="button" className={styles.actionButton} onClick={() => controller.toggleCustomLogic()}>
                  {pro.customLogic ? "Disable" : "Enable"} custom logic
                </button>
              </div>
            ) : (
              <div className={styles.locked}>
                Free tier keeps the first experience open. Pro unlocks deeper graph depth and full custom orchestration.
              </div>
            )}
          </article>
        </div>
      </section>
    </section>
  );
}
