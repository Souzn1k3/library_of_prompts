import type { RuntimeAction, ScenarioRuntimeTier } from "./types";
import { ScenarioRuntimeEngine } from "./ScenarioRuntimeEngine";

export class InteractionController {
  constructor(private readonly engine: ScenarioRuntimeEngine) {}

  dispatch(action: RuntimeAction): void {
    this.engine.dispatch(action);
  }

  hover(x: number, y: number): void {
    this.dispatch({ type: "hover", x, y });
  }

  click(x: number, y: number): void {
    this.dispatch({ type: "click", x, y });
  }

  touch(x: number, y: number): void {
    this.dispatch({ type: "touch", x, y });
  }

  keyboard(key: string): void {
    this.dispatch({ type: "keyboard", key });
  }

  setScenario(scenarioId: string): void {
    this.dispatch({ type: "switch-scenario", scenarioId });
  }

  setTier(tier: ScenarioRuntimeTier): void {
    this.dispatch({ type: "set-tier", tier });
  }

  toggleProPanel(): void {
    this.dispatch({ type: "toggle-pro-panel" });
  }

  setObjective(value: string): void {
    this.dispatch({ type: "set-objective", value });
  }

  setTemperature(value: number): void {
    this.dispatch({ type: "set-temperature", value });
  }

  setIntensity(value: number): void {
    this.dispatch({ type: "set-intensity", value });
  }

  setPrecision(value: number): void {
    this.dispatch({ type: "set-precision", value });
  }

  setAutomation(value: number): void {
    this.dispatch({ type: "set-automation", value });
  }

  setGraphDepth(value: number): void {
    this.dispatch({ type: "set-graph-depth", value });
  }

  toggleCustomLogic(): void {
    this.dispatch({ type: "toggle-custom-logic" });
  }

  generate(): void {
    this.dispatch({ type: "generate" });
  }

  pulse(): void {
    this.dispatch({ type: "pulse" });
  }
}
