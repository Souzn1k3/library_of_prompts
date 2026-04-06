import type { ScenarioDefinition, ScenarioRuntimeEvent, ScenarioTier } from "../types";
import { evaluateCondition, resolveValue } from "./utils";
import type { StateEngine } from "./state-engine";
import type { SandboxExecutor } from "./sandbox-executor";

type LogicEngineOptions = {
  definition: ScenarioDefinition;
  state: StateEngine;
  sandbox: SandboxExecutor;
  tier: ScenarioTier;
  now?: () => Date;
};

function tierWeight(tier: ScenarioTier): number {
  return tier === "pro" ? 2 : 1;
}

export class LogicEngine {
  private readonly stepsByEvent = new Map<string, typeof this.options.definition.logic.steps>();
  private readonly now: () => Date;

  constructor(private readonly options: LogicEngineOptions) {
    this.now = options.now ?? (() => new Date());
    for (const step of options.definition.logic.steps) {
      const events = Array.isArray(step.on) ? step.on : [step.on];
      for (const eventName of events) {
        const list = this.stepsByEvent.get(eventName) ?? [];
        list.push(step);
        this.stepsByEvent.set(eventName, list);
      }
    }
  }

  async handleEvent(event: ScenarioRuntimeEvent): Promise<ScenarioRuntimeEvent[]> {
    const usageAllowed = this.applyUsageAccounting(event);
    if (!usageAllowed) {
      return [];
    }

    const triggered = this.stepsByEvent.get(event.name) ?? [];
    if (!triggered.length) {
      return [];
    }

    const emittedEvents: ScenarioRuntimeEvent[] = [];

    for (const step of triggered) {
      if (!this.hasTierAccess(step.requiresTier)) {
        continue;
      }

      const snapshot = this.options.state.getSnapshot();
      const conditionPassed = evaluateCondition(step.condition, {
        snapshot,
        event,
      });
      if (!conditionPassed) {
        continue;
      }

      for (const action of step.actions) {
        if (action.kind === "invoke") {
          const input: Record<string, unknown> = {};
          for (const [key, value] of Object.entries(action.input ?? {})) {
            input[key] = resolveValue(value, {
              snapshot: this.options.state.getSnapshot(),
              event,
            });
          }

          try {
            const result = await this.options.sandbox.execute(action.actionId, input, {
              definition: this.options.definition,
              snapshot: this.options.state.getSnapshot(),
              event,
              tier: this.options.tier,
            });
            if (action.assign) {
              this.options.state.setValue(action.assign, result);
            }
          } catch (cause) {
            const message = cause instanceof Error ? cause.message : "Scenario action failed";
            this.options.state.pushError(message);
            if (action.onErrorAssign) {
              this.options.state.setValue(action.onErrorAssign, message);
            }
          }
          continue;
        }

        if (action.kind === "set") {
          const resolved = resolveValue(action.value, {
            snapshot: this.options.state.getSnapshot(),
            event,
          });
          this.options.state.setValue(action.target, resolved);
          continue;
        }

        if (action.kind === "set_path") {
          this.options.state.setPath(action.targetFrom, action.valueFrom, event);
          continue;
        }

        if (action.kind === "patch") {
          const resolved = resolveValue(action.value, {
            snapshot: this.options.state.getSnapshot(),
            event,
          });
          if (typeof resolved === "object" && resolved !== null && !Array.isArray(resolved)) {
            this.options.state.patchValue(action.target, resolved as Record<string, unknown>);
          }
          continue;
        }

        if (action.kind === "append") {
          const resolved = resolveValue(action.value, {
            snapshot: this.options.state.getSnapshot(),
            event,
          });
          this.options.state.appendValue(action.target, resolved);
          continue;
        }

        if (action.kind === "clear") {
          this.options.state.clearValue(action.target);
          continue;
        }

        if (action.kind === "emit") {
          const payload: Record<string, unknown> = {};
          for (const [key, value] of Object.entries(action.payload ?? {})) {
            payload[key] = resolveValue(value, {
              snapshot: this.options.state.getSnapshot(),
              event,
            });
          }
          emittedEvents.push({
            name: action.event,
            payload,
            at: this.now().toISOString(),
          });
          continue;
        }

        if (action.kind === "persist") {
          await this.options.state.persist(action.scope ?? "both");
          continue;
        }

        if (action.kind === "check_limit") {
          const limit = this.options.definition.permissions.usageLimits.find((item) => item.id === action.limitId);
          if (!limit) {
            continue;
          }
          const exceeded = this.options.state.isUsageLimitExceeded(limit.id, limit.max, limit.window);
          if (exceeded && action.ifExceededEvent) {
            emittedEvents.push({
              name: action.ifExceededEvent,
              payload: { limitId: limit.id, max: limit.max },
              at: this.now().toISOString(),
            });
          }
          continue;
        }
      }

      for (const transition of step.transitions ?? []) {
        const transitionPassed = evaluateCondition(transition.when, {
          snapshot: this.options.state.getSnapshot(),
          event,
        });
        if (!transitionPassed) {
          continue;
        }

        const payload: Record<string, unknown> = {};
        for (const [key, value] of Object.entries(transition.payload ?? {})) {
          payload[key] = resolveValue(value, {
            snapshot: this.options.state.getSnapshot(),
            event,
          });
        }

        emittedEvents.push({
          name: transition.event,
          payload,
          at: this.now().toISOString(),
        });
      }
    }

    return emittedEvents;
  }

  private hasTierAccess(required: ScenarioTier | undefined): boolean {
    if (!required) {
      return true;
    }
    return tierWeight(this.options.tier) >= tierWeight(required);
  }

  private applyUsageAccounting(event: ScenarioRuntimeEvent): boolean {
    const limits = this.options.definition.permissions.usageLimits.filter((limit) => limit.event === event.name);
    let allowed = true;
    for (const limit of limits) {
      const exceeded = this.options.state.isUsageLimitExceeded(limit.id, limit.max, limit.window);
      if (exceeded) {
        this.options.state.pushError(
          `Usage limit exceeded for "${limit.id}" (${limit.max}/${limit.window}).`,
        );
        allowed = false;
        continue;
      }
      this.options.state.incrementUsage(limit.id, limit.window);
    }
    return allowed;
  }
}
