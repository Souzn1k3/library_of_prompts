export type ScenarioRuntimeMode = "game" | "tool" | "ai";

export type ScenarioRuntimeTier = "free" | "pro";

export type ScenarioRuntimeSignal = "hover" | "click" | "keyboard" | "touch" | "text" | "system";

export type RuntimeScenario = {
  id: string;
  title: string;
  summary: string;
  category: string;
  monetization: "free" | "pro_only" | "paid";
  tags: string[];
  popularity: number;
};

export type RuntimeEntity = {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  hue: number;
  energy: number;
  highlighted: boolean;
};

export type RuntimePointerState = {
  x: number;
  y: number;
  inside: boolean;
};

export type ScenarioRuntimeMetric = {
  fps: number;
  interactions: number;
  reactionMs: number;
  loops: number;
  score: number;
};

export type ScenarioRuntimeFeedback = {
  title: string;
  detail: string;
  tone: "neutral" | "positive" | "warning";
  at: number;
};

export type ScenarioRuntimeTrace = {
  id: string;
  at: number;
  signal: ScenarioRuntimeSignal;
  detail: string;
};

export type ScenarioRuntimeCard = {
  id: string;
  label: string;
  value: string;
  tone: "neutral" | "positive" | "warning";
};

export type ScenarioExecutionContext = {
  sessionId: string;
  startedAt: number;
  lastInteractionAt: number;
  activeScenarioId: string;
  runtimeMode: ScenarioRuntimeMode;
  tier: ScenarioRuntimeTier;
};

export type ScenarioRuntimeState = {
  execution: ScenarioExecutionContext;
  runtimeMode: ScenarioRuntimeMode;
  tier: ScenarioRuntimeTier;
  stage: {
    width: number;
    height: number;
  };
  scenarios: RuntimeScenario[];
  activeScenarioId: string;
  pointer: RuntimePointerState;
  entities: RuntimeEntity[];
  metrics: ScenarioRuntimeMetric;
  result: {
    headline: string;
    summary: string;
    cards: ScenarioRuntimeCard[];
    stream: string[];
    streaming: boolean;
  };
  tool: {
    intensity: number;
    precision: number;
    automation: number;
  };
  game: {
    combo: number;
    energy: number;
  };
  ai: {
    objective: string;
    temperature: number;
  };
  pro: {
    panelOpen: boolean;
    graphDepth: number;
    customLogic: boolean;
  };
  feedback: ScenarioRuntimeFeedback;
  traces: ScenarioRuntimeTrace[];
};

export type RuntimeAction =
  | { type: "switch-scenario"; scenarioId: string }
  | { type: "hover"; x: number; y: number }
  | { type: "click"; x: number; y: number }
  | { type: "touch"; x: number; y: number }
  | { type: "keyboard"; key: string }
  | { type: "set-tier"; tier: ScenarioRuntimeTier }
  | { type: "toggle-pro-panel" }
  | { type: "set-objective"; value: string }
  | { type: "set-temperature"; value: number }
  | { type: "set-intensity"; value: number }
  | { type: "set-precision"; value: number }
  | { type: "set-automation"; value: number }
  | { type: "set-graph-depth"; value: number }
  | { type: "toggle-custom-logic" }
  | { type: "generate" }
  | { type: "pulse" };

export const DEFAULT_STAGE_SIZE = {
  width: 1440,
  height: 880,
} as const;

export const DEFAULT_SCENARIOS: RuntimeScenario[] = [
  {
    id: "runtime-revenue-pulse",
    title: "Revenue Pulse",
    summary: "Tool runtime: steer growth levers and observe immediate KPI reactions.",
    category: "growth",
    monetization: "free",
    tags: ["tool", "growth", "kpi"],
    popularity: 88,
  },
  {
    id: "runtime-ops-arena",
    title: "Ops Arena",
    summary: "Game runtime: click and redirect moving signals to keep system stable.",
    category: "entertainment",
    monetization: "pro_only",
    tags: ["game", "arena", "signals"],
    popularity: 74,
  },
  {
    id: "runtime-agent-flow",
    title: "Agent Flow",
    summary: "AI runtime: stream generation and steer objective without leaving execution.",
    category: "learning",
    monetization: "paid",
    tags: ["ai", "generation", "stream"],
    popularity: 81,
  },
];

export function resolveRuntimeMode(scenario: RuntimeScenario): ScenarioRuntimeMode {
  const category = scenario.category.toLowerCase();
  if (category.includes("entertain")) {
    return "game";
  }
  if (category.includes("learn") || category.includes("ai")) {
    return "ai";
  }
  return "tool";
}
