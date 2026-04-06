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

  const chain = [parent, ...children];
  const merged: ScenarioDefinition = {
    ...parent,
    layout: {
      ...parent.layout,
      panels: dedupeByKey(chain.flatMap((definition) => definition.layout.panels), (node) => node.id),
      canvas: dedupeByKey(
        chain.flatMap((definition) => definition.layout.canvas ?? []),
        (node) => node.id,
      ),
      controls: dedupeByKey(
        chain.flatMap((definition) => definition.layout.controls ?? []),
        (node) => node.id,
      ),
    },
    inputs: {
      fields: dedupeByKey(chain.flatMap((definition) => definition.inputs.fields), (field) => field.id),
      interactions: dedupeByKey(
        chain.flatMap((definition) => definition.inputs.interactions),
        (interaction) => interaction.id,
      ),
    },
    logic: {
      entryEvents: dedupeStrings(chain.flatMap((definition) => definition.logic.entryEvents)),
      steps: dedupeByKey(chain.flatMap((definition) => definition.logic.steps), (step) => step.id),
    },
    state: {
      ...parent.state,
      variables: dedupeByKey(
        chain.flatMap((definition) => definition.state.variables),
        (variable) => `${variable.scope}:${variable.key}`,
      ),
    },
    permissions: {
      ...parent.permissions,
      gates: dedupeByKey(chain.flatMap((definition) => definition.permissions.gates), (gate) => gate.id),
      usageLimits: dedupeByKey(
        chain.flatMap((definition) => definition.permissions.usageLimits),
        (limit) => limit.id,
      ),
    },
    sandbox: {
      ...parent.sandbox,
      allowedActions: dedupeStrings(
        chain.flatMap((definition) => definition.sandbox?.allowedActions ?? []),
      ),
    },
    composition: {
      pipeline: dedupeStrings(chain.flatMap((definition) => definition.composition?.pipeline ?? [])),
      sharedState: dedupeByKey(
        chain.flatMap((definition) => definition.composition?.sharedState ?? []),
        (binding) => `${binding.from}->${binding.to}`,
      ),
    },
  };

  return merged;
}

function dedupeStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const deduped: string[] = [];
  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    deduped.push(value);
  }
  return deduped;
}

function dedupeByKey<T>(
  values: T[],
  keySelector: (value: T) => string,
): T[] {
  const seen = new Set<string>();
  const deduped: T[] = [];
  for (const value of values) {
    const key = keySelector(value);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(value);
  }
  return deduped;
}
