import type {
  ScenarioDefinition,
  ScenarioInteractionDefinition,
  ScenarioRuntimeEvent,
  ScenarioRuntimeSnapshot,
} from "../types";
import { resolveValue } from "./utils";

type InteractionDispatch = (eventName: string, payload?: Record<string, unknown>) => Promise<void>;

type InteractionEngineOptions = {
  definition: ScenarioDefinition;
  dispatch: InteractionDispatch;
  getSnapshot: () => ScenarioRuntimeSnapshot;
  now?: () => Date;
};

export class InteractionEngine {
  private readonly byId = new Map<string, ScenarioInteractionDefinition>();
  private readonly now: () => Date;

  constructor(private readonly options: InteractionEngineOptions) {
    this.now = options.now ?? (() => new Date());
    for (const interaction of options.definition.inputs.interactions) {
      this.byId.set(interaction.id, interaction);
    }
  }

  getInteraction(interactionId: string): ScenarioInteractionDefinition | null {
    return this.byId.get(interactionId) ?? null;
  }

  async trigger(interactionId: string, rawPayload?: Record<string, unknown>): Promise<void> {
    const interaction = this.byId.get(interactionId);
    if (!interaction) {
      return;
    }

    const payload = this.resolvePayload(interaction, rawPayload ?? {});
    await this.options.dispatch(interaction.emits, payload);
  }

  private resolvePayload(
    interaction: ScenarioInteractionDefinition,
    rawPayload: Record<string, unknown>,
  ): Record<string, unknown> {
    if (!interaction.payload) {
      return rawPayload;
    }

    const event: ScenarioRuntimeEvent = {
      name: "__interaction__",
      payload: rawPayload,
      at: this.now().toISOString(),
    };
    const snapshot = this.options.getSnapshot();
    const payload: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(interaction.payload)) {
      payload[key] = resolveValue(value, {
        snapshot,
        event,
        interactionPayload: rawPayload,
      });
    }

    return payload;
  }
}
