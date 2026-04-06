import type {
  ScenarioDefinition,
  ScenarioRuntimeEvent,
  ScenarioRuntimeSnapshot,
  ScenarioStateVariable,
} from "../types";
import { clearByPathImmutable, cloneSnapshot, deepEqual, getByPath, setByPathImmutable } from "./utils";

export type ScenarioPersistenceAdapter = {
  load: (key: string) => Promise<Partial<ScenarioRuntimeSnapshot> | null>;
  save: (key: string, snapshot: ScenarioRuntimeSnapshot) => Promise<void>;
};

type StateEngineOptions = {
  definition: ScenarioDefinition;
  persistenceAdapter?: ScenarioPersistenceAdapter;
  now?: () => Date;
};

type PersistScope = "local" | "server" | "both";

const HISTORY_LIMIT = 120;

function nowIso(now: () => Date): string {
  return now().toISOString();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function mergeObjects(base: unknown, patch: unknown): unknown {
  if (!isRecord(base) || !isRecord(patch)) {
    return patch;
  }
  const next: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(patch)) {
    next[key] = mergeObjects(next[key], value);
  }
  return next;
}

function applyVariableDefaults(snapshot: ScenarioRuntimeSnapshot, variable: ScenarioStateVariable): ScenarioRuntimeSnapshot {
  const scopePath = `${variable.scope}.${variable.key}`;
  return setByPathImmutable(snapshot, scopePath, variable.initial);
}

export class StateEngine {
  private snapshot: ScenarioRuntimeSnapshot;
  private readonly initialSnapshot: ScenarioRuntimeSnapshot;
  private readonly listeners = new Set<() => void>();
  private readonly past: ScenarioRuntimeSnapshot[] = [];
  private readonly future: ScenarioRuntimeSnapshot[] = [];
  private readonly now: () => Date;

  constructor(private readonly options: StateEngineOptions) {
    this.now = options.now ?? (() => new Date());
    this.snapshot = this.buildInitialSnapshot();
    this.restoreLocalPersistence();
    this.initialSnapshot = cloneSnapshot(this.snapshot);
  }

  getSnapshot(): ScenarioRuntimeSnapshot {
    return this.snapshot;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  recordEvent(event: ScenarioRuntimeEvent): void {
    this.mutate((current) => {
      const replay = [...current.replay, event];
      return {
        ...current,
        replay,
        meta: {
          ...current.meta,
          lastEvent: event.name,
          eventCount: current.meta.eventCount + 1,
          lastUpdatedAt: event.at,
        },
      };
    });
  }

  setValue(path: string, value: unknown): void {
    this.mutate((current) => setByPathImmutable(current, path, value));
  }

  setPath(pathFrom: string, valueFrom: string, event: ScenarioRuntimeEvent): void {
    const targetPath = getByPath(event.payload, pathFrom) ?? getByPath(event, pathFrom);
    const nextValue = getByPath(event.payload, valueFrom) ?? getByPath(event, valueFrom);
    if (typeof targetPath !== "string" || !targetPath.trim()) {
      return;
    }
    this.setValue(targetPath, nextValue);
  }

  patchValue(path: string, patch: Record<string, unknown>): void {
    this.mutate((current) => {
      const currentValue = getByPath(current, path);
      const nextValue = mergeObjects(currentValue, patch);
      return setByPathImmutable(current, path, nextValue);
    });
  }

  appendValue(path: string, value: unknown): void {
    this.mutate((current) => {
      const currentValue = getByPath(current, path);
      const arrayValue = Array.isArray(currentValue) ? currentValue : [];
      return setByPathImmutable(current, path, [...arrayValue, value]);
    });
  }

  clearValue(path: string): void {
    this.mutate((current) => clearByPathImmutable(current, path));
  }

  clearErrors(): void {
    this.setValue("errors", []);
  }

  pushError(message: string): void {
    this.appendValue("errors", message);
  }

  isUsageLimitExceeded(limitId: string, max: number, window: "session" | "day"): boolean {
    const usage = this.getUsageEntry(limitId);
    if (!usage) {
      return false;
    }
    if (window === "day") {
      const currentDay = nowIso(this.now).slice(0, 10);
      const usageDay = usage.windowStartedAt.slice(0, 10);
      if (usageDay !== currentDay) {
        return false;
      }
    }
    return usage.count >= max;
  }

  incrementUsage(limitId: string, window: "session" | "day"): void {
    this.mutate((current) => {
      const key = `usage.${limitId}`;
      const entry = (getByPath(current, key) as { count: number; windowStartedAt: string } | undefined) ?? null;
      const now = nowIso(this.now);

      let nextEntry = entry;
      if (!entry) {
        nextEntry = { count: 1, windowStartedAt: now };
      } else if (window === "day" && entry.windowStartedAt.slice(0, 10) !== now.slice(0, 10)) {
        nextEntry = { count: 1, windowStartedAt: now };
      } else {
        nextEntry = { count: entry.count + 1, windowStartedAt: entry.windowStartedAt };
      }

      return setByPathImmutable(current, key, nextEntry);
    });
  }

  undo(): boolean {
    if (!this.options.definition.state.enableUndoRedo || !this.past.length) {
      return false;
    }
    const previous = this.past.pop();
    if (!previous) {
      return false;
    }
    this.future.push(cloneSnapshot(this.snapshot));
    this.snapshot = previous;
    this.notify();
    return true;
  }

  redo(): boolean {
    if (!this.options.definition.state.enableUndoRedo || !this.future.length) {
      return false;
    }
    const next = this.future.pop();
    if (!next) {
      return false;
    }
    this.past.push(cloneSnapshot(this.snapshot));
    this.snapshot = next;
    this.notify();
    return true;
  }

  replayLog(): ScenarioRuntimeEvent[] {
    return this.snapshot.replay;
  }

  resetToInitial(): void {
    this.snapshot = cloneSnapshot(this.initialSnapshot);
    this.past.length = 0;
    this.future.length = 0;
    this.notify();
  }

  async hydrateFromServer(): Promise<void> {
    if (!this.options.definition.state.persistence.server || !this.options.persistenceAdapter) {
      return;
    }

    const key = this.persistenceKey();
    const saved = await this.options.persistenceAdapter.load(key);
    if (!saved) {
      return;
    }

    this.mutate((current) => mergeObjects(current, saved) as ScenarioRuntimeSnapshot, false);
  }

  async persist(scope: PersistScope): Promise<void> {
    const persistence = this.options.definition.state.persistence;
    const key = this.persistenceKey();

    if ((scope === "local" || scope === "both") && persistence.local && typeof window !== "undefined") {
      try {
        window.localStorage.setItem(key, JSON.stringify(this.snapshot));
      } catch {
        // Ignore storage quota and availability failures.
      }
    }

    if ((scope === "server" || scope === "both") && persistence.server && this.options.persistenceAdapter) {
      await this.options.persistenceAdapter.save(key, this.snapshot);
    }
  }

  private buildInitialSnapshot(): ScenarioRuntimeSnapshot {
    let snapshot: ScenarioRuntimeSnapshot = {
      global: {},
      local: {},
      session: {},
      ui: {},
      streams: {},
      usage: {},
      errors: [],
      replay: [],
      meta: {
        lastEvent: null,
        eventCount: 0,
        lastUpdatedAt: null,
      },
    };

    for (const variable of this.options.definition.state.variables) {
      snapshot = applyVariableDefaults(snapshot, variable);
    }

    for (const field of this.options.definition.inputs.fields) {
      const hasValue = getByPath(snapshot, field.bind) !== undefined;
      if (hasValue) {
        continue;
      }
      snapshot = setByPathImmutable(snapshot, field.bind, field.defaultValue ?? "");
    }

    return snapshot;
  }

  private restoreLocalPersistence(): void {
    if (!this.options.definition.state.persistence.local || typeof window === "undefined") {
      return;
    }

    const key = this.persistenceKey();
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return;
    }

    try {
      const parsed = JSON.parse(raw) as Partial<ScenarioRuntimeSnapshot>;
      this.snapshot = mergeObjects(this.snapshot, parsed) as ScenarioRuntimeSnapshot;
    } catch {
      // Ignore malformed persistence payload.
    }
  }

  private mutate(
    updater: (current: ScenarioRuntimeSnapshot) => ScenarioRuntimeSnapshot,
    trackHistory = true,
  ): void {
    const current = this.snapshot;
    const next = updater(current);
    if (deepEqual(current, next)) {
      return;
    }

    if (trackHistory && this.options.definition.state.enableUndoRedo) {
      this.past.push(cloneSnapshot(current));
      if (this.past.length > HISTORY_LIMIT) {
        this.past.shift();
      }
      this.future.length = 0;
    }

    this.snapshot = {
      ...next,
      meta: {
        ...next.meta,
        lastUpdatedAt: nowIso(this.now),
      },
    };
    this.notify();
  }

  private getUsageEntry(limitId: string): { count: number; windowStartedAt: string } | null {
    const usage = getByPath(this.snapshot, `usage.${limitId}`);
    if (!isRecord(usage) || typeof usage.count !== "number" || typeof usage.windowStartedAt !== "string") {
      return null;
    }
    return {
      count: usage.count,
      windowStartedAt: usage.windowStartedAt,
    };
  }

  private notify(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  private persistenceKey(): string {
    return `scenario-engine:${this.options.definition.state.persistence.key}`;
  }
}
