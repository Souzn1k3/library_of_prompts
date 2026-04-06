import type {
  ScenarioCondition,
  ScenarioRuntimeEvent,
  ScenarioRuntimeSnapshot,
  ScenarioValueRef,
} from "../types";

type ResolveContext = {
  snapshot: ScenarioRuntimeSnapshot;
  event: ScenarioRuntimeEvent;
  interactionPayload?: Record<string, unknown>;
  extras?: Record<string, unknown>;
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function structuredCloneSafe<T>(value: T): T {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value)) as T;
}

function toPathSegments(path: string): string[] {
  return path
    .split(".")
    .map((segment) => segment.trim())
    .filter(Boolean);
}

export function getByPath(target: unknown, path: string): unknown {
  if (!path) {
    return target;
  }
  let current: unknown = target;
  for (const segment of toPathSegments(path)) {
    if (current === null || current === undefined) {
      return undefined;
    }
    if (!isObject(current) && !Array.isArray(current)) {
      return undefined;
    }
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}

export function setByPathImmutable<T>(target: T, path: string, value: unknown): T {
  const segments = toPathSegments(path);
  if (!segments.length) {
    return value as T;
  }

  const root = isObject(target) || Array.isArray(target) ? structuredCloneSafe(target) : ({} as T);
  let cursor: unknown = root;

  for (let index = 0; index < segments.length; index += 1) {
    const segment = segments[index];
    const isLeaf = index === segments.length - 1;

    if (!isObject(cursor) && !Array.isArray(cursor)) {
      return root;
    }

    if (isLeaf) {
      (cursor as Record<string, unknown>)[segment] = value;
      continue;
    }

    const next = (cursor as Record<string, unknown>)[segment];
    if (isObject(next) || Array.isArray(next)) {
      cursor = next;
      continue;
    }

    (cursor as Record<string, unknown>)[segment] = {};
    cursor = (cursor as Record<string, unknown>)[segment];
  }

  return root;
}

export function clearByPathImmutable<T>(target: T, path: string): T {
  const segments = toPathSegments(path);
  if (!segments.length) {
    return target;
  }

  const root = structuredCloneSafe(target);
  let cursor: unknown = root;

  for (let index = 0; index < segments.length; index += 1) {
    const segment = segments[index];
    const isLeaf = index === segments.length - 1;

    if (!isObject(cursor)) {
      return root;
    }

    if (isLeaf) {
      delete (cursor as Record<string, unknown>)[segment];
      return root;
    }

    cursor = (cursor as Record<string, unknown>)[segment];
  }

  return root;
}

function resolveFromPath(path: string, context: ResolveContext): unknown {
  if (path.startsWith("event.payload.")) {
    return getByPath(context.event.payload, path.slice("event.payload.".length));
  }
  if (path === "event.name") {
    return context.event.name;
  }
  if (path.startsWith("interaction.")) {
    return getByPath(context.interactionPayload ?? {}, path.slice("interaction.".length));
  }
  if (path.startsWith("state.")) {
    return getByPath(context.snapshot, path.slice("state.".length));
  }
  if (path.startsWith("extras.")) {
    return getByPath(context.extras ?? {}, path.slice("extras.".length));
  }
  return getByPath(context.snapshot, path);
}

function resolveTemplate(template: string, context: ResolveContext): string {
  return template.replaceAll(/\{\{([^}]+)\}\}/g, (_, rawPath: string) => {
    const value = resolveFromPath(rawPath.trim(), context);
    if (value === null || value === undefined) {
      return "";
    }
    return String(value);
  });
}

export function resolveValue(value: ScenarioValueRef, context: ResolveContext): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => resolveValue(item, context));
  }

  if (!isObject(value)) {
    return value;
  }

  if ("from" in value && typeof value.from === "string") {
    const resolved = resolveFromPath(value.from, context);
    if (resolved === undefined) {
      return value.fallback === undefined ? undefined : resolveValue(value.fallback, context);
    }
    return resolved;
  }

  if ("template" in value && typeof value.template === "string") {
    return resolveTemplate(value.template, context);
  }

  const next: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    next[key] = resolveValue(item as ScenarioValueRef, context);
  }
  return next;
}

function compareUnknown(value: unknown, other: unknown): number | null {
  if (typeof value === "number" && typeof other === "number") {
    return value - other;
  }
  if (typeof value === "string" && typeof other === "string") {
    return value.localeCompare(other);
  }
  return null;
}

export function evaluateCondition(
  condition: ScenarioCondition | undefined,
  context: ResolveContext,
): boolean {
  if (!condition) {
    return true;
  }

  if (condition.all?.length) {
    return condition.all.every((item) => evaluateCondition(item, context));
  }

  if (condition.any?.length) {
    return condition.any.some((item) => evaluateCondition(item, context));
  }

  if (condition.not) {
    return !evaluateCondition(condition.not, context);
  }

  const value = condition.path ? resolveFromPath(condition.path, context) : undefined;

  if (condition.exists !== undefined) {
    const exists = value !== null && value !== undefined;
    if (exists !== condition.exists) {
      return false;
    }
  }

  if (condition.equals !== undefined && value !== condition.equals) {
    return false;
  }

  if (condition.notEquals !== undefined && value === condition.notEquals) {
    return false;
  }

  if (condition.in && !condition.in.includes(value)) {
    return false;
  }

  if (condition.gt !== undefined) {
    const cmp = compareUnknown(value, condition.gt);
    if (cmp === null || cmp <= 0) {
      return false;
    }
  }

  if (condition.gte !== undefined) {
    const cmp = compareUnknown(value, condition.gte);
    if (cmp === null || cmp < 0) {
      return false;
    }
  }

  if (condition.lt !== undefined) {
    const cmp = compareUnknown(value, condition.lt);
    if (cmp === null || cmp >= 0) {
      return false;
    }
  }

  if (condition.lte !== undefined) {
    const cmp = compareUnknown(value, condition.lte);
    if (cmp === null || cmp > 0) {
      return false;
    }
  }

  return true;
}

export function deepEqual(left: unknown, right: unknown): boolean {
  if (left === right) {
    return true;
  }

  if (typeof left !== typeof right) {
    return false;
  }

  if (Array.isArray(left) && Array.isArray(right)) {
    if (left.length !== right.length) {
      return false;
    }
    return left.every((item, index) => deepEqual(item, right[index]));
  }

  if (isObject(left) && isObject(right)) {
    const leftKeys = Object.keys(left);
    const rightKeys = Object.keys(right);
    if (leftKeys.length !== rightKeys.length) {
      return false;
    }
    return leftKeys.every((key) => deepEqual(left[key], right[key]));
  }

  return false;
}

export function cloneSnapshot<T>(value: T): T {
  return structuredCloneSafe(value);
}
