import type { ScenarioDefinition, ScenarioLayoutNode } from "../types";

export class LayoutEngine {
  private readonly panelIndex: Map<string, ScenarioLayoutNode> = new Map();

  constructor(private readonly definition: ScenarioDefinition) {
    for (const panel of definition.layout.panels) {
      this.indexNode(panel);
    }
  }

  getRootPanels(): ScenarioLayoutNode[] {
    return this.definition.layout.panels;
  }

  getNode(nodeId: string): ScenarioLayoutNode | null {
    return this.panelIndex.get(nodeId) ?? null;
  }

  private indexNode(node: ScenarioLayoutNode): void {
    this.panelIndex.set(node.id, node);

    if ("children" in node && Array.isArray(node.children)) {
      for (const child of node.children) {
        this.indexNode(child);
      }
    }
  }
}

export function composeScenarioDefinitions(
  parent: ScenarioDefinition,
  children: ScenarioDefinition[],
): ScenarioDefinition {
  if (!children.length) {
    return parent;
  }

  const merged: ScenarioDefinition = {
    ...parent,
    layout: {
      ...parent.layout,
      panels: [...parent.layout.panels],
    },
    inputs: {
      fields: [...parent.inputs.fields],
      interactions: [...parent.inputs.interactions],
    },
    logic: {
      entryEvents: [...parent.logic.entryEvents],
      steps: [...parent.logic.steps],
    },
    state: {
      ...parent.state,
      variables: [...parent.state.variables],
    },
  };

  for (const child of children) {
    merged.layout.panels.push(...child.layout.panels);
    merged.inputs.fields.push(...child.inputs.fields);
    merged.inputs.interactions.push(...child.inputs.interactions);
    merged.logic.entryEvents.push(...child.logic.entryEvents);
    merged.logic.steps.push(...child.logic.steps);
    merged.state.variables.push(...child.state.variables);
  }

  return merged;
}
