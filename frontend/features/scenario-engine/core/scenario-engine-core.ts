import type {
  ScenarioActionRegistry,
  ScenarioDefinition,
  ScenarioRuntimeEvent,
  ScenarioRuntimeSnapshot,
  ScenarioTier,
} from "../types";
import { InteractionEngine } from "./interaction-engine";
import { LayoutEngine } from "./layout-engine";
import { LogicEngine } from "./logic-engine";
import { SandboxExecutor } from "./sandbox-executor";
import { StateEngine, type ScenarioPersistenceAdapter } from "./state-engine";

type ScenarioEngineCoreOptions = {
  definition: ScenarioDefinition;
  actions: ScenarioActionRegistry;
  tier?: ScenarioTier;
  persistenceAdapter?: ScenarioPersistenceAdapter;
  now?: () => Date;
};

const MAX_EVENT_CHAIN = 160;

function tierWeight(tier: ScenarioTier): number {
  return tier === "pro" ? 2 : 1;
}

export class ScenarioEngineCore {
  readonly layout: LayoutEngine;
  readonly state: StateEngine;
  readonly logic: LogicEngine;
  readonly interaction: InteractionEngine;
  private readonly sandbox: SandboxExecutor;
  private readonly now: () => Date;
  private readonly tier: ScenarioTier;
  private autosaveTimer: ReturnType<typeof setTimeout> | null = null;
  private processedEventsInMinute = 0;
  private minuteWindowStartedAt = 0;

  constructor(private readonly options: ScenarioEngineCoreOptions) {
    this.now = options.now ?? (() => new Date());
    this.tier = options.tier ?? options.definition.permissions.defaultTier;
    this.layout = new LayoutEngine(options.definition);
    this.state = new StateEngine({
      definition: options.definition,
      persistenceAdapter: options.persistenceAdapter,
      now: this.now,
    });
    this.sandbox = new SandboxExecutor({
      definition: options.definition,
      actions: options.actions,
    });
    this.logic = new LogicEngine({
      definition: options.definition,
      state: this.state,
      sandbox: this.sandbox,
      tier: this.tier,
      now: this.now,
    });
    this.interaction = new InteractionEngine({
      definition: options.definition,
      dispatch: async (eventName, payload) => {
        await this.dispatch(eventName, payload ?? {});
      },
      getSnapshot: () => this.state.getSnapshot(),
      now: this.now,
    });
  }

  get definition(): ScenarioDefinition {
    return this.options.definition;
  }

  getSnapshot(): ScenarioRuntimeSnapshot {
    return this.state.getSnapshot();
  }

  subscribe(listener: () => void): () => void {
    return this.state.subscribe(listener);
  }

  async boot(): Promise<void> {
    await this.state.hydrateFromServer();
    for (const eventName of this.options.definition.logic.entryEvents) {
      await this.dispatch(eventName, {});
    }

    const resumeEvent = this.options.definition.state.resumeEvent;
    if (resumeEvent && this.options.definition.state.enableReplay) {
      await this.dispatch(resumeEvent, {});
    }
  }

  async dispatch(eventName: string, payload: Record<string, unknown>): Promise<void> {
    if (this.exceedsSandboxRate()) {
      this.state.pushError("Scenario sandbox rate limit reached. Please wait and retry.");
      return;
    }

    const queue: ScenarioRuntimeEvent[] = [
      {
        name: eventName,
        payload,
        at: this.now().toISOString(),
      },
    ];
    let processed = 0;

    while (queue.length && processed < MAX_EVENT_CHAIN) {
      const event = queue.shift();
      if (!event) {
        break;
      }
      processed += 1;

      this.state.recordEvent(event);
      const emitted = await this.logic.handleEvent(event);
      queue.push(...emitted);
    }

    if (processed >= MAX_EVENT_CHAIN) {
      this.state.pushError("Scenario event chain exceeded safety limit and was truncated.");
    }

    this.scheduleAutosave();
  }

  async triggerInteraction(interactionId: string, payload?: Record<string, unknown>): Promise<void> {
    await this.interaction.trigger(interactionId, payload);
  }

  getPermissionMessage(gateId: string | undefined): string | null {
    if (!gateId) {
      return null;
    }
    const gate = this.options.definition.permissions.gates.find((item) => item.id === gateId);
    if (!gate) {
      return null;
    }
    return tierWeight(this.tier) >= tierWeight(gate.requires) ? null : gate.message;
  }

  undo(): boolean {
    return this.state.undo();
  }

  redo(): boolean {
    return this.state.redo();
  }

  replayEvents(): ScenarioRuntimeEvent[] {
    return this.state.replayLog();
  }

  async resume(): Promise<void> {
    const resumeEvent = this.options.definition.state.resumeEvent;
    if (!resumeEvent) {
      return;
    }
    await this.dispatch(resumeEvent, {});
  }

  async persistNow(): Promise<void> {
    const persistence = this.options.definition.state.persistence;
    if (!persistence.local && !persistence.server) {
      return;
    }
    const scope = persistence.local && persistence.server ? "both" : persistence.local ? "local" : "server";
    await this.state.persist(scope);
  }

  private scheduleAutosave(): void {
    const autosaveMs = this.options.definition.state.persistence.autosaveMs;
    if (!autosaveMs || autosaveMs <= 0) {
      return;
    }
    if (this.autosaveTimer) {
      clearTimeout(this.autosaveTimer);
    }
    this.autosaveTimer = setTimeout(() => {
      void this.persistNow();
      this.autosaveTimer = null;
    }, autosaveMs);
  }

  private exceedsSandboxRate(): boolean {
    const maxEventsPerMinute = this.options.definition.sandbox?.maxEventsPerMinute;
    if (!maxEventsPerMinute) {
      return false;
    }

    const nowMs = this.now().getTime();
    if (!this.minuteWindowStartedAt || nowMs - this.minuteWindowStartedAt > 60_000) {
      this.minuteWindowStartedAt = nowMs;
      this.processedEventsInMinute = 0;
    }

    this.processedEventsInMinute += 1;
    return this.processedEventsInMinute > maxEventsPerMinute;
  }
}
