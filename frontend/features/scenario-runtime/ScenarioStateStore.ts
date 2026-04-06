import { createJSONStorage, persist } from "zustand/middleware";
import { createStore, type StoreApi } from "zustand/vanilla";

import {
  DEFAULT_SCENARIOS,
  DEFAULT_STAGE_SIZE,
  resolveRuntimeMode,
  type RuntimeEntity,
  type RuntimeScenario,
  type ScenarioRuntimeCard,
  type ScenarioRuntimeMode,
  type ScenarioRuntimeState,
  type ScenarioRuntimeTier,
} from "./types";

const LOCAL_STORAGE_KEY = "scenario-runtime-local-v1";
const SESSION_STORAGE_KEY = "scenario-runtime-session-v1";

const MAX_TRACE_ROWS = 34;

type ScenarioRuntimeSessionState = {
  activeScenarioId: string;
  runtimeMode: ScenarioRuntimeMode;
  tier: ScenarioRuntimeTier;
  proPanelOpen: boolean;
};

function randomSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `runtime-${Math.random().toString(16).slice(2)}-${Date.now().toString(16)}`;
}

function seedRange(index: number, max: number): number {
  return ((index * 173) % 997) / 997 * max;
}

export function createRuntimeEntities(mode: ScenarioRuntimeMode, count = 18): RuntimeEntity[] {
  const entities: RuntimeEntity[] = [];
  for (let index = 0; index < count; index += 1) {
    const lane = index % 6;
    const row = Math.floor(index / 6);
    const x = 140 + lane * 210 + seedRange(index, 28);
    const y = 150 + row * 190 + seedRange(index + 41, 26);
    const speedScale = mode === "game" ? 1.5 : mode === "ai" ? 1.2 : 1;
    entities.push({
      id: `entity-${index + 1}`,
      x,
      y,
      vx: (Math.sin(index * 0.93) * 0.42 + 0.18) * speedScale,
      vy: (Math.cos(index * 0.71) * 0.35 + 0.14) * speedScale,
      radius: mode === "game" ? 18 + (index % 4) * 3 : 14 + (index % 5) * 2,
      hue: (index * 27 + (mode === "ai" ? 170 : mode === "game" ? 28 : 210)) % 360,
      energy: 0.32 + ((index * 37) % 100) / 120,
      highlighted: false,
    });
  }
  return entities;
}

function describeMode(mode: ScenarioRuntimeMode): { headline: string; summary: string } {
  if (mode === "game") {
    return {
      headline: "Game loop armed",
      summary: "Redirect moving signals and maintain system balance in real time.",
    };
  }
  if (mode === "ai") {
    return {
      headline: "AI stream is live",
      summary: "Objective control and streaming result are now inside the runtime.",
    };
  }
  return {
    headline: "Tool runtime active",
    summary: "Manipulate levers and watch KPIs change instantly.",
  };
}

function createResultCards(mode: ScenarioRuntimeMode): ScenarioRuntimeCard[] {
  if (mode === "game") {
    return [
      { id: "card-combo", label: "Combo", value: "x1", tone: "neutral" },
      { id: "card-energy", label: "Stability", value: "86%", tone: "positive" },
      { id: "card-window", label: "Reaction", value: "<120 ms", tone: "positive" },
    ];
  }
  if (mode === "ai") {
    return [
      { id: "card-tokens", label: "Stream", value: "ready", tone: "neutral" },
      { id: "card-steps", label: "Steps", value: "5", tone: "positive" },
      { id: "card-edit", label: "Editable", value: "yes", tone: "positive" },
    ];
  }
  return [
    { id: "card-latency", label: "Latency", value: "92 ms", tone: "positive" },
    { id: "card-conversion", label: "Conversion", value: "+12.4%", tone: "positive" },
    { id: "card-integrity", label: "Integrity", value: "99.2%", tone: "neutral" },
  ];
}

function createInitialState(seedScenarios: RuntimeScenario[]): ScenarioRuntimeState {
  const scenarios = seedScenarios.length ? seedScenarios : DEFAULT_SCENARIOS;
  const activeScenarioId = scenarios[0]?.id ?? "runtime-default";
  const mode = resolveRuntimeMode(scenarios[0] ?? DEFAULT_SCENARIOS[0]);
  const now = Date.now();
  const modeCopy = describeMode(mode);

  return {
    execution: {
      sessionId: randomSessionId(),
      startedAt: now,
      lastInteractionAt: now,
      activeScenarioId,
      runtimeMode: mode,
      tier: "free",
    },
    runtimeMode: mode,
    tier: "free",
    stage: {
      width: DEFAULT_STAGE_SIZE.width,
      height: DEFAULT_STAGE_SIZE.height,
    },
    scenarios,
    activeScenarioId,
    pointer: {
      x: DEFAULT_STAGE_SIZE.width / 2,
      y: DEFAULT_STAGE_SIZE.height / 2,
      inside: false,
    },
    entities: createRuntimeEntities(mode),
    metrics: {
      fps: 60,
      interactions: 0,
      reactionMs: 0,
      loops: 0,
      score: 0,
    },
    result: {
      headline: modeCopy.headline,
      summary: modeCopy.summary,
      cards: createResultCards(mode),
      stream: [
        "runtime boot complete",
        "interaction loop waiting for signal",
      ],
      streaming: false,
    },
    tool: {
      intensity: 62,
      precision: 58,
      automation: 41,
    },
    game: {
      combo: 1,
      energy: 86,
    },
    ai: {
      objective: "Launch resilient scenario runtime",
      temperature: 0.62,
    },
    pro: {
      panelOpen: false,
      graphDepth: 2,
      customLogic: false,
    },
    feedback: {
      title: "Runtime ready",
      detail: "Click or move on stage to trigger execution flow.",
      tone: "neutral",
      at: now,
    },
    traces: [
      {
        id: "trace-init",
        at: now,
        signal: "system",
        detail: "ScenarioRuntimeEngine booted and waiting for input.",
      },
    ],
  };
}

function pickScenarioById(scenarios: RuntimeScenario[], scenarioId: string): RuntimeScenario {
  return scenarios.find((item) => item.id === scenarioId) ?? scenarios[0] ?? DEFAULT_SCENARIOS[0];
}

export class ScenarioStateStore {
  readonly api: StoreApi<ScenarioRuntimeState>;
  private sessionPersistTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(seedScenarios: RuntimeScenario[] = DEFAULT_SCENARIOS) {
    this.api = createStore<ScenarioRuntimeState>()(
      persist(
        () => createInitialState(seedScenarios),
        {
          name: LOCAL_STORAGE_KEY,
          storage: createJSONStorage(() => localStorage),
          partialize: (state) => ({
            tier: state.tier,
            tool: state.tool,
            ai: state.ai,
            pro: {
              graphDepth: state.pro.graphDepth,
              customLogic: state.pro.customLogic,
              panelOpen: state.pro.panelOpen,
            },
          }),
        },
      ),
    );

    this.hydrateSessionState();
  }

  getState(): ScenarioRuntimeState {
    return this.api.getState();
  }

  subscribe(listener: (state: ScenarioRuntimeState) => void): () => void {
    return this.api.subscribe(listener);
  }

  setScenarios(nextScenarios: RuntimeScenario[]): void {
    const fallback = nextScenarios.length ? nextScenarios : DEFAULT_SCENARIOS;
    this.update((state) => {
      const canKeepActive = fallback.some((item) => item.id === state.activeScenarioId);
      const targetScenario = pickScenarioById(
        fallback,
        canKeepActive ? state.activeScenarioId : fallback[0]?.id ?? DEFAULT_SCENARIOS[0].id,
      );
      const mode = resolveRuntimeMode(targetScenario);
      const modeCopy = describeMode(mode);
      return {
        ...state,
        scenarios: fallback,
        activeScenarioId: targetScenario.id,
        runtimeMode: mode,
        execution: {
          ...state.execution,
          activeScenarioId: targetScenario.id,
          runtimeMode: mode,
        },
        result: {
          ...state.result,
          headline: modeCopy.headline,
          summary: modeCopy.summary,
          cards: createResultCards(mode),
        },
        entities: createRuntimeEntities(mode),
      };
    });
  }

  selectScenario(scenarioId: string): void {
    this.update((state) => {
      const selected = pickScenarioById(state.scenarios, scenarioId);
      const mode = resolveRuntimeMode(selected);
      const now = Date.now();
      const modeCopy = describeMode(mode);
      return {
        ...state,
        activeScenarioId: selected.id,
        runtimeMode: mode,
        entities: createRuntimeEntities(mode),
        execution: {
          ...state.execution,
          activeScenarioId: selected.id,
          runtimeMode: mode,
          lastInteractionAt: now,
        },
        result: {
          ...state.result,
          headline: `${selected.title} runtime active`,
          summary: modeCopy.summary,
          cards: createResultCards(mode),
          stream: [
            "scenario switched",
            `${selected.title} loaded in ${mode} mode`,
          ],
          streaming: false,
        },
        feedback: {
          title: "Scenario switched",
          detail: `${selected.title} selected. Runtime mode: ${mode}.`,
          tone: "positive",
          at: now,
        },
      };
    });
  }

  setTier(tier: ScenarioRuntimeTier): void {
    this.update((state) => {
      const now = Date.now();
      return {
        ...state,
        tier,
        execution: {
          ...state.execution,
          tier,
          lastInteractionAt: now,
        },
        feedback: {
          title: tier === "pro" ? "Pro logic unlocked" : "Free mode active",
          detail:
            tier === "pro"
              ? "Advanced graph depth and custom orchestration are now available."
              : "Core runtime remains fully interactive in free mode.",
          tone: tier === "pro" ? "positive" : "neutral",
          at: now,
        },
      };
    });
  }

  update(updater: (state: ScenarioRuntimeState) => ScenarioRuntimeState): void {
    const next = updater(this.api.getState());
    this.api.setState(next, true);
    this.scheduleSessionPersist();
  }

  patch(partial: Partial<ScenarioRuntimeState>): void {
    this.api.setState(partial);
    this.scheduleSessionPersist();
  }

  private hydrateSessionState(): void {
    if (typeof window === "undefined") {
      return;
    }
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw) as ScenarioRuntimeSessionState;
      this.update((state) => {
        const scenario = pickScenarioById(state.scenarios, parsed.activeScenarioId);
        const mode = resolveRuntimeMode(scenario);
        return {
          ...state,
          activeScenarioId: scenario.id,
          runtimeMode: parsed.runtimeMode ?? mode,
          tier: parsed.tier ?? state.tier,
          pro: {
            ...state.pro,
            panelOpen: parsed.proPanelOpen ?? state.pro.panelOpen,
          },
          execution: {
            ...state.execution,
            activeScenarioId: scenario.id,
            runtimeMode: parsed.runtimeMode ?? mode,
            tier: parsed.tier ?? state.tier,
          },
          entities: createRuntimeEntities(parsed.runtimeMode ?? mode),
        };
      });
    } catch {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }

  private scheduleSessionPersist(): void {
    if (typeof window === "undefined") {
      return;
    }
    if (this.sessionPersistTimer) {
      clearTimeout(this.sessionPersistTimer);
    }
    this.sessionPersistTimer = setTimeout(() => {
      const state = this.api.getState();
      const payload: ScenarioRuntimeSessionState = {
        activeScenarioId: state.activeScenarioId,
        runtimeMode: state.runtimeMode,
        tier: state.tier,
        proPanelOpen: state.pro.panelOpen,
      };
      window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(payload));
      this.sessionPersistTimer = null;
    }, 80);
  }
}

export function pushTrace(
  traces: ScenarioRuntimeState["traces"],
  detail: string,
  signal: ScenarioRuntimeState["traces"][number]["signal"],
): ScenarioRuntimeState["traces"] {
  const next = [
    {
      id: `trace-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
      at: Date.now(),
      signal,
      detail,
    },
    ...traces,
  ];
  return next.slice(0, MAX_TRACE_ROWS);
}
