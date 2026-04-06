import type { ScenarioRenderer } from "./ScenarioRenderer";
import { ScenarioStateStore, pushTrace } from "./ScenarioStateStore";
import { resolveRuntimeMode, type RuntimeAction, type RuntimeEntity, type ScenarioRuntimeState } from "./types";

const COMMIT_INTERVAL_MS = 120;
const STREAM_TICK_MS = 110;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function distance(ax: number, ay: number, bx: number, by: number): number {
  return Math.hypot(ax - bx, ay - by);
}

function formatNumber(value: number): string {
  return Number.isFinite(value) ? value.toFixed(1) : "0.0";
}

function cloneEntities(entities: RuntimeEntity[]): RuntimeEntity[] {
  return entities.map((entity) => ({ ...entity }));
}

function deriveCards(state: ScenarioRuntimeState): ScenarioRuntimeState["result"]["cards"] {
  if (state.runtimeMode === "game") {
    return [
      { id: "combo", label: "Combo", value: `x${state.game.combo}`, tone: "positive" },
      { id: "energy", label: "Stability", value: `${Math.round(state.game.energy)}%`, tone: state.game.energy > 62 ? "positive" : "warning" },
      { id: "score", label: "Score", value: Math.round(state.metrics.score).toString(), tone: "neutral" },
    ];
  }
  if (state.runtimeMode === "ai") {
    return [
      { id: "temp", label: "Temp", value: formatNumber(state.ai.temperature), tone: "neutral" },
      { id: "tokens", label: "Stream lines", value: String(state.result.stream.length), tone: "positive" },
      { id: "depth", label: "Graph depth", value: String(state.pro.graphDepth), tone: state.tier === "pro" ? "positive" : "warning" },
    ];
  }
  return [
    { id: "intensity", label: "Intensity", value: `${state.tool.intensity}%`, tone: "neutral" },
    { id: "precision", label: "Precision", value: `${state.tool.precision}%`, tone: "positive" },
    { id: "automation", label: "Automation", value: `${state.tool.automation}%`, tone: state.tool.automation > 70 ? "positive" : "neutral" },
  ];
}

function deriveSummary(state: ScenarioRuntimeState): string {
  if (state.runtimeMode === "game") {
    return `Hit moving signals to keep stability above 60%. Current combo: x${state.game.combo}.`;
  }
  if (state.runtimeMode === "ai") {
    return `Streaming ${state.result.streaming ? "in progress" : "ready"}. Objective: ${state.ai.objective}.`;
  }
  return `Live levers applied. Intensity ${state.tool.intensity}% and precision ${state.tool.precision}% are driving this runtime.`;
}

export class ScenarioRuntimeEngine {
  private renderer: ScenarioRenderer | null = null;
  private animationFrameId: number | null = null;
  private aiStreamTimer: ReturnType<typeof setInterval> | null = null;
  private generateDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  private running = false;
  private frameCounter = 0;
  private fpsAccumulator = 0;
  private lastFrameAt = 0;
  private lastCommitAt = 0;
  private liveEntities: RuntimeEntity[] = [];

  constructor(private readonly stateStore: ScenarioStateStore) {
    this.liveEntities = cloneEntities(this.stateStore.getState().entities);
  }

  start(): void {
    if (this.running) {
      return;
    }
    this.running = true;
    this.lastFrameAt = 0;
    this.lastCommitAt = 0;
    this.frameCounter = 0;
    this.fpsAccumulator = 0;
    this.liveEntities = cloneEntities(this.stateStore.getState().entities);
    this.animationFrameId = requestAnimationFrame(this.loop);
  }

  stop(): void {
    this.running = false;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.aiStreamTimer) {
      clearInterval(this.aiStreamTimer);
      this.aiStreamTimer = null;
    }
    if (this.generateDebounceTimer) {
      clearTimeout(this.generateDebounceTimer);
      this.generateDebounceTimer = null;
    }
  }

  attachRenderer(renderer: ScenarioRenderer): void {
    this.renderer = renderer;
  }

  detachRenderer(renderer?: ScenarioRenderer): void {
    if (renderer && renderer !== this.renderer) {
      return;
    }
    this.renderer = null;
  }

  dispatch(action: RuntimeAction): void {
    const startedAt = performance.now();

    switch (action.type) {
      case "switch-scenario": {
        this.stateStore.selectScenario(action.scenarioId);
        this.liveEntities = cloneEntities(this.stateStore.getState().entities);
        this.startStream("scenario-switch");
        break;
      }
      case "set-tier": {
        this.stateStore.setTier(action.tier);
        this.registerInteraction("click", `tier switched to ${action.tier}`, startedAt);
        break;
      }
      case "toggle-pro-panel": {
        this.stateStore.update((state) => ({
          ...state,
          pro: {
            ...state.pro,
            panelOpen: !state.pro.panelOpen,
          },
          feedback: {
            title: state.pro.panelOpen ? "Pro panel hidden" : "Pro panel opened",
            detail: state.pro.panelOpen
              ? "Focus returned to core runtime stage."
              : "Advanced graph controls are now visible below.",
            tone: "neutral",
            at: Date.now(),
          },
        }));
        this.registerInteraction("click", "toggled pro panel", startedAt);
        break;
      }
      case "hover": {
        this.applyHover(action.x, action.y, startedAt, "hover");
        break;
      }
      case "touch": {
        this.applyClick(action.x, action.y, startedAt, "touch");
        break;
      }
      case "click": {
        this.applyClick(action.x, action.y, startedAt, "click");
        break;
      }
      case "keyboard": {
        this.handleKeyboard(action.key, startedAt);
        break;
      }
      case "set-objective": {
        this.stateStore.update((state) => ({
          ...state,
          ai: {
            ...state.ai,
            objective: action.value,
          },
          result: {
            ...state.result,
            summary: deriveSummary({
              ...state,
              ai: {
                ...state.ai,
                objective: action.value,
              },
            }),
          },
        }));
        this.scheduleAutoGenerate();
        this.registerInteraction("text", "objective edited", startedAt);
        break;
      }
      case "set-temperature": {
        this.stateStore.update((state) => {
          const nextState: ScenarioRuntimeState = {
            ...state,
            ai: {
              ...state.ai,
              temperature: clamp(action.value, 0.05, 1),
            },
          };
          return {
            ...nextState,
            result: {
              ...nextState.result,
              cards: deriveCards(nextState),
              summary: deriveSummary(nextState),
            },
          };
        });
        this.scheduleAutoGenerate();
        this.registerInteraction("text", "temperature changed", startedAt);
        break;
      }
      case "set-intensity": {
        this.applyToolChange("intensity", action.value, startedAt);
        break;
      }
      case "set-precision": {
        this.applyToolChange("precision", action.value, startedAt);
        break;
      }
      case "set-automation": {
        this.applyToolChange("automation", action.value, startedAt);
        break;
      }
      case "set-graph-depth": {
        const state = this.stateStore.getState();
        if (state.tier !== "pro") {
          this.stateStore.update((current) => ({
            ...current,
            feedback: {
              title: "Pro depth locked",
              detail: "Graph depth above 2 is available in pro mode.",
              tone: "warning",
              at: Date.now(),
            },
          }));
          this.registerInteraction("click", "blocked graph depth change", startedAt);
          break;
        }
        this.stateStore.update((current) => {
          const nextState: ScenarioRuntimeState = {
            ...current,
            pro: {
              ...current.pro,
              graphDepth: clamp(Math.round(action.value), 1, 6),
            },
          };
          return {
            ...nextState,
            result: {
              ...nextState.result,
              cards: deriveCards(nextState),
            },
            feedback: {
              title: "Graph depth updated",
              detail: `Execution graph now runs ${nextState.pro.graphDepth} layers deep.`,
              tone: "positive",
              at: Date.now(),
            },
          };
        });
        this.startStream("graph-depth");
        this.registerInteraction("click", "graph depth changed", startedAt);
        break;
      }
      case "toggle-custom-logic": {
        this.stateStore.update((state) => {
          if (state.tier !== "pro") {
            return {
              ...state,
              feedback: {
                title: "Custom logic locked",
                detail: "Switch to pro mode to unlock full scenario graph editing.",
                tone: "warning",
                at: Date.now(),
              },
            };
          }

          const customLogic = !state.pro.customLogic;
          return {
            ...state,
            pro: {
              ...state.pro,
              customLogic,
            },
            feedback: {
              title: customLogic ? "Custom logic enabled" : "Custom logic disabled",
              detail: customLogic
                ? "Deep orchestration is now participating in execution transitions."
                : "Runtime is back to baseline orchestration.",
              tone: customLogic ? "positive" : "neutral",
              at: Date.now(),
            },
          };
        });
        this.startStream("custom-logic");
        this.registerInteraction("click", "custom logic toggled", startedAt);
        break;
      }
      case "generate": {
        this.startStream("manual-generate");
        this.registerInteraction("click", "manual stream generation", startedAt);
        break;
      }
      case "pulse": {
        this.applyPulse(startedAt);
        break;
      }
      default: {
        break;
      }
    }
  }

  private loop = (timestamp: number) => {
    if (!this.running) {
      return;
    }

    if (!this.lastFrameAt) {
      this.lastFrameAt = timestamp;
      this.lastCommitAt = timestamp;
    }

    const delta = clamp(timestamp - this.lastFrameAt, 8, 40);
    this.lastFrameAt = timestamp;
    this.frameCounter += 1;
    this.fpsAccumulator += 1000 / delta;

    const state = this.stateStore.getState();
    const speedMultiplier = state.runtimeMode === "game" ? 1.2 : state.runtimeMode === "ai" ? 1.08 : 0.95;
    const pointerInfluence = state.pointer.inside ? 0.0007 : 0;

    for (const entity of this.liveEntities) {
      if (pointerInfluence > 0) {
        const dx = state.pointer.x - entity.x;
        const dy = state.pointer.y - entity.y;
        entity.vx += dx * pointerInfluence;
        entity.vy += dy * pointerInfluence;
      }

      entity.x += entity.vx * delta * speedMultiplier;
      entity.y += entity.vy * delta * speedMultiplier;

      const damping = 0.994;
      entity.vx *= damping;
      entity.vy *= damping;

      if (entity.x <= entity.radius || entity.x >= state.stage.width - entity.radius) {
        entity.vx *= -1;
        entity.x = clamp(entity.x, entity.radius, state.stage.width - entity.radius);
      }
      if (entity.y <= entity.radius || entity.y >= state.stage.height - entity.radius) {
        entity.vy *= -1;
        entity.y = clamp(entity.y, entity.radius, state.stage.height - entity.radius);
      }

      entity.energy = clamp(entity.energy * 0.997, 0.2, 1.8);
      if (!entity.highlighted) {
        continue;
      }
      entity.energy = clamp(entity.energy + 0.004, 0.2, 2.4);
    }

    this.renderer?.render(
      {
        ...state,
        entities: this.liveEntities,
      },
      timestamp,
    );

    if (timestamp - this.lastCommitAt >= COMMIT_INTERVAL_MS) {
      const avgFps = this.fpsAccumulator / Math.max(1, this.frameCounter);
      const loops = state.metrics.loops + this.frameCounter;
      this.stateStore.update((current) => ({
        ...current,
        entities: cloneEntities(this.liveEntities),
        metrics: {
          ...current.metrics,
          fps: Number(avgFps.toFixed(1)),
          loops,
        },
      }));
      this.frameCounter = 0;
      this.fpsAccumulator = 0;
      this.lastCommitAt = timestamp;
    }

    this.animationFrameId = requestAnimationFrame(this.loop);
  };

  private handleKeyboard(key: string, startedAt: number): void {
    const normalized = key.toLowerCase();
    if (normalized === " " || normalized === "spacebar") {
      this.applyPulse(startedAt);
      return;
    }

    if (normalized === "p") {
      const tier = this.stateStore.getState().tier;
      this.dispatch({ type: "set-tier", tier: tier === "pro" ? "free" : "pro" });
      return;
    }

    if (normalized === "d") {
      this.dispatch({ type: "toggle-pro-panel" });
      return;
    }

    if (normalized === "1" || normalized === "2" || normalized === "3") {
      const state = this.stateStore.getState();
      const index = Math.max(0, Math.min(state.scenarios.length - 1, Number(normalized) - 1));
      const scenario = state.scenarios[index];
      if (scenario) {
        this.dispatch({ type: "switch-scenario", scenarioId: scenario.id });
      }
      return;
    }

    this.registerInteraction("keyboard", `key ${normalized}`, startedAt);
  }

  private applyHover(x: number, y: number, startedAt: number, signal: "hover"): void {
    for (const entity of this.liveEntities) {
      const d = distance(x, y, entity.x, entity.y);
      entity.highlighted = d < entity.radius * 2.15;
      if (entity.highlighted) {
        entity.energy = clamp(entity.energy + 0.08, 0.2, 2.3);
      }
    }

    this.stateStore.update((state) => ({
      ...state,
      pointer: {
        x,
        y,
        inside: true,
      },
    }));

    this.registerInteraction(signal, "pointer hover", startedAt, false);
  }

  private applyClick(x: number, y: number, startedAt: number, signal: "click" | "touch"): void {
    let hitCount = 0;

    for (const entity of this.liveEntities) {
      const dx = entity.x - x;
      const dy = entity.y - y;
      const d = Math.max(0.001, Math.hypot(dx, dy));
      const influence = Math.max(0, (280 - d) / 280);
      if (influence <= 0) {
        continue;
      }
      hitCount += 1;
      entity.vx += (dx / d) * influence * 2.8;
      entity.vy += (dy / d) * influence * 2.8;
      entity.energy = clamp(entity.energy + influence * 0.6, 0.2, 2.6);
      entity.highlighted = true;
    }

    this.stateStore.update((state) => {
      const scoreGain = hitCount * (state.runtimeMode === "game" ? 11 : 4);
      const combo = state.runtimeMode === "game" ? clamp(state.game.combo + 1, 1, 99) : state.game.combo;
      const energy = clamp(state.game.energy + hitCount * 0.5, 28, 99);
      const interactions = state.metrics.interactions + 1;
      const nextState: ScenarioRuntimeState = {
        ...state,
        pointer: {
          x,
          y,
          inside: true,
        },
        metrics: {
          ...state.metrics,
          interactions,
          score: state.metrics.score + scoreGain,
        },
        game: {
          combo,
          energy,
        },
      };
      return {
        ...nextState,
        result: {
          ...nextState.result,
          cards: deriveCards(nextState),
          summary: deriveSummary(nextState),
        },
        feedback: {
          title: hitCount > 0 ? "Signal captured" : "No signal hit",
          detail: hitCount > 0
            ? `Affected nodes: ${hitCount}. Runtime reacted immediately.`
            : "Try clicking closer to active moving nodes.",
          tone: hitCount > 0 ? "positive" : "warning",
          at: Date.now(),
        },
      };
    });

    this.registerInteraction(signal, `click impact ${hitCount}`, startedAt);
  }

  private applyToolChange(kind: "intensity" | "precision" | "automation", value: number, startedAt: number): void {
    this.stateStore.update((state) => {
      const bounded = Math.round(clamp(value, 0, 100));
      const tool = {
        ...state.tool,
        [kind]: bounded,
      };

      const nextState: ScenarioRuntimeState = {
        ...state,
        tool,
      };

      return {
        ...nextState,
        result: {
          ...nextState.result,
          cards: deriveCards(nextState),
          summary: deriveSummary(nextState),
        },
        feedback: {
          title: `${kind} adjusted`,
          detail: `${kind} is now ${bounded}%. Output was recomputed instantly.`,
          tone: "positive",
          at: Date.now(),
        },
      };
    });

    this.registerInteraction("text", `${kind} changed`, startedAt);
    this.scheduleAutoGenerate();
  }

  private applyPulse(startedAt: number): void {
    const state = this.stateStore.getState();
    const centerX = state.stage.width / 2;
    const centerY = state.stage.height / 2;

    this.applyClick(centerX, centerY, startedAt, "click");

    this.stateStore.update((current) => ({
      ...current,
      result: {
        ...current.result,
        stream: [
          "pulse injected from control center",
          ...current.result.stream,
        ].slice(0, 32),
      },
    }));

    this.registerInteraction("keyboard", "pulse action", startedAt);
  }

  private scheduleAutoGenerate(): void {
    if (this.generateDebounceTimer) {
      clearTimeout(this.generateDebounceTimer);
    }
    this.generateDebounceTimer = setTimeout(() => {
      this.startStream("auto-regenerate");
      this.generateDebounceTimer = null;
    }, 260);
  }

  private startStream(reason: string): void {
    if (this.aiStreamTimer) {
      clearInterval(this.aiStreamTimer);
      this.aiStreamTimer = null;
    }

    const snapshot = this.stateStore.getState();
    const mode = snapshot.runtimeMode;
    const lines = [
      `mode=${mode}`,
      `scenario=${snapshot.execution.activeScenarioId}`,
      `reason=${reason}`,
      `objective=${snapshot.ai.objective}`,
      `intensity=${snapshot.tool.intensity} precision=${snapshot.tool.precision}`,
      `tier=${snapshot.tier} graphDepth=${snapshot.pro.graphDepth}`,
      "pipeline: input -> state -> render -> feedback",
      "status: runtime execution synchronized",
    ];

    let index = 0;
    this.stateStore.update((state) => ({
      ...state,
      result: {
        ...state.result,
        stream: [],
        streaming: true,
      },
    }));

    this.aiStreamTimer = setInterval(() => {
      const state = this.stateStore.getState();
      if (index >= lines.length) {
        clearInterval(this.aiStreamTimer!);
        this.aiStreamTimer = null;
        this.stateStore.update((current) => ({
          ...current,
          result: {
            ...current.result,
            streaming: false,
            summary: deriveSummary(current),
            cards: deriveCards(current),
          },
          feedback: {
            title: "Stream complete",
            detail: "Runtime output regenerated and remains editable.",
            tone: "positive",
            at: Date.now(),
          },
        }));
        return;
      }

      const line = `${state.result.stream.length + 1}. ${lines[index]}`;
      index += 1;
      this.stateStore.update((current) => ({
        ...current,
        result: {
          ...current.result,
          stream: [line, ...current.result.stream].slice(0, 24),
          streaming: true,
        },
      }));
    }, STREAM_TICK_MS);
  }

  private registerInteraction(
    signal: ScenarioRuntimeState["traces"][number]["signal"],
    detail: string,
    startedAt: number,
    withTrace = true,
  ): void {
    const reactionMs = Math.max(1, performance.now() - startedAt);

    this.stateStore.update((state) => {
      const next = {
        ...state,
        execution: {
          ...state.execution,
          lastInteractionAt: Date.now(),
        },
        metrics: {
          ...state.metrics,
          interactions: signal === "hover" ? state.metrics.interactions : state.metrics.interactions + 1,
          reactionMs: Number(reactionMs.toFixed(1)),
        },
      };

      return {
        ...next,
        traces: withTrace ? pushTrace(next.traces, detail, signal) : next.traces,
      };
    });
  }

  syncEntitiesFromState(): void {
    this.liveEntities = cloneEntities(this.stateStore.getState().entities);
  }

  hydrateMarketplaceScenarios(
    scenarios: Array<{
      id: string;
      title: string;
      summary: string | null;
      category: string;
      monetization_mode: string;
      tags: string[];
      run_count: number;
      like_count: number;
    }>,
  ): void {
    if (!scenarios.length) {
      return;
    }

    const normalized = scenarios.slice(0, 9).map((row) => {
      const monetization: "free" | "pro_only" | "paid" =
        row.monetization_mode === "paid"
          ? "paid"
          : row.monetization_mode === "pro_only"
            ? "pro_only"
            : "free";

      return {
        id: row.id,
        title: row.title,
        summary: row.summary ?? "Live runtime scenario",
        category: row.category,
        monetization,
        tags: row.tags,
        popularity: row.run_count + row.like_count,
      };
    });

    this.stateStore.setScenarios(normalized);
    this.syncEntitiesFromState();

    const active = this.stateStore.getState();
    const scenario = normalized.find((item) => item.id === active.activeScenarioId) ?? normalized[0];
    const mode = resolveRuntimeMode(scenario);
    this.stateStore.update((state) => ({
      ...state,
      runtimeMode: mode,
      execution: {
        ...state.execution,
        runtimeMode: mode,
      },
      result: {
        ...state.result,
        headline: `${scenario.title} runtime active`,
        summary: deriveSummary({
          ...state,
          runtimeMode: mode,
        }),
      },
      traces: pushTrace(state.traces, "marketplace scenarios hydrated", "system"),
    }));
  }
}
