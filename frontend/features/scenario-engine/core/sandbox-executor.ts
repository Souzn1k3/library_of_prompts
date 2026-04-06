import type {
  ScenarioActionExecutionContext,
  ScenarioActionHandler,
  ScenarioActionRegistry,
  ScenarioDefinition,
} from "../types";

export class ScenarioSandboxError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ScenarioSandboxError";
  }
}

type SandboxOptions = {
  definition: ScenarioDefinition;
  actions: ScenarioActionRegistry;
};

export class SandboxExecutor {
  private readonly timeoutMs: number;
  private readonly allowlist: Set<string>;

  constructor(private readonly options: SandboxOptions) {
    this.timeoutMs = options.definition.sandbox?.maxActionMs ?? 5000;
    this.allowlist = new Set(options.definition.sandbox?.allowedActions ?? Object.keys(options.actions));
  }

  async execute(
    actionId: string,
    payload: Record<string, unknown>,
    context: ScenarioActionExecutionContext,
  ): Promise<unknown> {
    if (!this.allowlist.has(actionId)) {
      throw new ScenarioSandboxError(`Action "${actionId}" is blocked by sandbox allowlist.`);
    }

    const handler: ScenarioActionHandler | undefined = this.options.actions[actionId];
    if (!handler) {
      throw new ScenarioSandboxError(`Action "${actionId}" is not registered.`);
    }

    const execution = Promise.resolve(handler(payload, context));
    const timeout = new Promise<never>((_, reject) => {
      const id = setTimeout(() => {
        clearTimeout(id);
        reject(new ScenarioSandboxError(`Action "${actionId}" exceeded ${this.timeoutMs}ms.`));
      }, this.timeoutMs);
    });

    return Promise.race([execution, timeout]);
  }
}
