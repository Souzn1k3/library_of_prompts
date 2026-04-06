export type ScenarioAppType = "game" | "tool" | "ai" | "hybrid";

export type ScenarioRendererType = "dom" | "canvas" | "stream" | "hybrid";

export type ScenarioEventType = "click" | "input" | "drag" | "keyboard" | "submit" | "custom";

export type ScenarioTier = "free" | "pro";

export type ScenarioValueRef =
  | string
  | number
  | boolean
  | null
  | Array<ScenarioValueRef>
  | { [key: string]: ScenarioValueRef }
  | {
      from: string;
      fallback?: ScenarioValueRef;
    }
  | {
      template: string;
    };

export type ScenarioCondition = {
  all?: ScenarioCondition[];
  any?: ScenarioCondition[];
  not?: ScenarioCondition;
  path?: string;
  equals?: unknown;
  notEquals?: unknown;
  in?: unknown[];
  gt?: number;
  gte?: number;
  lt?: number;
  lte?: number;
  exists?: boolean;
};

export type ScenarioInteractionDefinition = {
  id: string;
  type: ScenarioEventType;
  source: string;
  emits: string;
  payload?: Record<string, ScenarioValueRef>;
};

export type ScenarioInputFieldType =
  | "text"
  | "textarea"
  | "number"
  | "date"
  | "select"
  | "checkbox"
  | "hidden";

export type ScenarioInputOption = {
  label: string;
  value: string;
};

export type ScenarioInputField = {
  id: string;
  formId: string;
  label: string;
  type: ScenarioInputFieldType;
  bind: string;
  placeholder?: string;
  required?: boolean;
  min?: number;
  step?: number;
  options?: ScenarioInputOption[];
  defaultValue?: string | number | boolean | null;
  inputMode?: "text" | "numeric" | "decimal";
  interactionId: string;
};

export type ScenarioPermissionGate = {
  id: string;
  requires: ScenarioTier;
  message: string;
  deniedEvent?: string;
};

export type ScenarioUsageLimit = {
  id: string;
  event: string;
  max: number;
  window: "session" | "day";
};

export type ScenarioStateVariable = {
  key: string;
  scope: "global" | "local" | "session" | "ui" | "streams";
  initial: ScenarioValueRef;
};

export type ScenarioStateDefinition = {
  variables: ScenarioStateVariable[];
  persistence: {
    key: string;
    local: boolean;
    server: boolean;
    autosaveMs?: number;
  };
  enableUndoRedo?: boolean;
  enableReplay?: boolean;
  resumeEvent?: string;
};

export type ScenarioLogicAction =
  | {
      kind: "invoke";
      actionId: string;
      input?: Record<string, ScenarioValueRef>;
      assign?: string;
      onErrorAssign?: string;
    }
  | {
      kind: "set";
      target: string;
      value: ScenarioValueRef;
    }
  | {
      kind: "set_path";
      targetFrom: string;
      valueFrom: string;
    }
  | {
      kind: "patch";
      target: string;
      value: Record<string, ScenarioValueRef>;
    }
  | {
      kind: "append";
      target: string;
      value: ScenarioValueRef;
    }
  | {
      kind: "emit";
      event: string;
      payload?: Record<string, ScenarioValueRef>;
    }
  | {
      kind: "persist";
      scope?: "local" | "server" | "both";
    }
  | {
      kind: "check_limit";
      limitId: string;
      ifExceededEvent?: string;
    }
  | {
      kind: "clear";
      target: string;
    };

export type ScenarioLogicTransition = {
  event: string;
  when?: ScenarioCondition;
  payload?: Record<string, ScenarioValueRef>;
};

export type ScenarioLogicStep = {
  id: string;
  on: string | string[];
  requiresTier?: ScenarioTier;
  condition?: ScenarioCondition;
  actions: ScenarioLogicAction[];
  transitions?: ScenarioLogicTransition[];
};

export type ScenarioLogicDefinition = {
  entryEvents: string[];
  steps: ScenarioLogicStep[];
};

export type ScenarioShellTab = {
  id: string;
  label: string;
  interactionId?: string;
};

export type ScenarioLayoutNodeBase = {
  id: string;
  renderer: ScenarioRendererType;
  visibleWhen?: ScenarioCondition;
  gateId?: string;
  className?: string;
  interactionSource?: string;
  keyboardFocusable?: boolean;
  draggable?: boolean;
};

export type ScenarioContainerNode = ScenarioLayoutNodeBase & {
  kind: "container";
  direction: "stack" | "grid";
  columns?: number;
  children: ScenarioLayoutNode[];
};

export type ScenarioSectionNode = ScenarioLayoutNodeBase & {
  kind: "section";
  title?: string;
  subtitle?: string;
  children: ScenarioLayoutNode[];
};

export type ScenarioHeroNode = ScenarioLayoutNodeBase & {
  kind: "hero";
  kicker?: string;
  title: string;
  subtitle?: string;
  meta?: string;
  tabs?: ScenarioShellTab[];
};

export type ScenarioTextNode = ScenarioLayoutNodeBase & {
  kind: "text";
  text: string;
  tone?: "normal" | "success" | "warning" | "danger";
};

export type ScenarioActionButton = {
  id: string;
  label: string;
  interactionId: string;
  tone?: "primary" | "secondary";
  disabledWhen?: ScenarioCondition;
};

export type ScenarioActionsNode = ScenarioLayoutNodeBase & {
  kind: "actions";
  actions: ScenarioActionButton[];
};

export type ScenarioMetricItem = {
  id: string;
  label: string;
  value: ScenarioValueRef;
  format?: "percent" | "usd" | "number" | "text";
  fallback?: string;
};

export type ScenarioMetricGridNode = ScenarioLayoutNodeBase & {
  kind: "metric_grid";
  items: ScenarioMetricItem[];
  columns?: number;
};

export type ScenarioCardField = {
  key: string;
  label?: string;
  format?: "percent" | "usd" | "number" | "text";
  fallback?: string;
};

export type ScenarioCardListNode = ScenarioLayoutNodeBase & {
  kind: "card_list";
  title?: string;
  subtitle?: string;
  source: string;
  emptyText?: string;
  titleField?: string;
  subtitleField?: string;
  fields: ScenarioCardField[];
  columns?: number;
};

export type ScenarioTableColumn = {
  key: string;
  label: string;
  format?: "percent" | "usd" | "number" | "text";
  fallback?: string;
};

export type ScenarioTableNode = ScenarioLayoutNodeBase & {
  kind: "table";
  title?: string;
  subtitle?: string;
  source: string;
  columns: ScenarioTableColumn[];
  emptyText?: string;
};

export type ScenarioFormNode = ScenarioLayoutNodeBase & {
  kind: "form";
  formId: string;
  title?: string;
  subtitle?: string;
  fieldIds: string[];
  submitLabel: string;
  submitInteractionId: string;
};

export type ScenarioStreamNode = ScenarioLayoutNodeBase & {
  kind: "stream";
  source: string;
  maxLines?: number;
  emptyText?: string;
};

export type ScenarioCanvasNode = ScenarioLayoutNodeBase & {
  kind: "canvas";
  source: string;
  chart: "bars" | "line" | "dots";
  width?: number;
  height?: number;
};

export type ScenarioHybridNode = ScenarioLayoutNodeBase & {
  kind: "hybrid";
  children: ScenarioLayoutNode[];
};

export type ScenarioLayoutNode =
  | ScenarioContainerNode
  | ScenarioSectionNode
  | ScenarioHeroNode
  | ScenarioTextNode
  | ScenarioActionsNode
  | ScenarioMetricGridNode
  | ScenarioCardListNode
  | ScenarioTableNode
  | ScenarioFormNode
  | ScenarioStreamNode
  | ScenarioCanvasNode
  | ScenarioHybridNode;

export type ScenarioLayoutDefinition = {
  panels: ScenarioLayoutNode[];
  canvas?: ScenarioLayoutNode[];
  controls?: ScenarioLayoutNode[];
};

export type ScenarioOutputDefinition = {
  renderer: ScenarioRendererType;
  liveUpdates: boolean;
  streamPath?: string;
};

export type ScenarioPermissionsDefinition = {
  defaultTier: ScenarioTier;
  gates: ScenarioPermissionGate[];
  usageLimits: ScenarioUsageLimit[];
};

export type ScenarioCompositionBinding = {
  from: string;
  to: string;
};

export type ScenarioCompositionDefinition = {
  pipeline?: string[];
  sharedState?: ScenarioCompositionBinding[];
};

export type ScenarioSandboxDefinition = {
  allowedActions: string[];
  maxActionMs?: number;
  maxEventsPerMinute?: number;
};

export type ScenarioDefinition = {
  id: string;
  type: ScenarioAppType;
  version: number;
  title: string;
  description: string;
  layout: ScenarioLayoutDefinition;
  inputs: {
    fields: ScenarioInputField[];
    interactions: ScenarioInteractionDefinition[];
  };
  logic: ScenarioLogicDefinition;
  output: ScenarioOutputDefinition;
  state: ScenarioStateDefinition;
  permissions: ScenarioPermissionsDefinition;
  composition?: ScenarioCompositionDefinition;
  sandbox?: ScenarioSandboxDefinition;
};

export type ScenarioRuntimeEvent = {
  name: string;
  payload: Record<string, unknown>;
  at: string;
};

export type ScenarioRuntimeSnapshot = {
  global: Record<string, unknown>;
  local: Record<string, unknown>;
  session: Record<string, unknown>;
  ui: Record<string, unknown>;
  streams: Record<string, string[]>;
  usage: Record<string, { count: number; windowStartedAt: string }>;
  errors: string[];
  replay: ScenarioRuntimeEvent[];
  meta: {
    lastEvent: string | null;
    eventCount: number;
    lastUpdatedAt: string | null;
  };
};

export type ScenarioActionExecutionContext = {
  definition: ScenarioDefinition;
  snapshot: ScenarioRuntimeSnapshot;
  event: ScenarioRuntimeEvent;
  tier: ScenarioTier;
};

export type ScenarioActionHandler = (
  input: Record<string, unknown>,
  context: ScenarioActionExecutionContext,
) => Promise<unknown> | unknown;

export type ScenarioActionRegistry = Record<string, ScenarioActionHandler>;
