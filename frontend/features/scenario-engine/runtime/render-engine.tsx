"use client";

import { useMemo } from "react";
import type {
  DragEventHandler,
  KeyboardEventHandler,
  MouseEventHandler,
  ReactNode,
} from "react";

import type { ScenarioEngineCore } from "../core/scenario-engine-core";
import { evaluateCondition, getByPath, resolveValue } from "../core/utils";
import type {
  ScenarioActionButton,
  ScenarioInputField,
  ScenarioLayoutNode,
  ScenarioRuntimeSnapshot,
} from "../types";

type RenderContext = {
  engine: ScenarioEngineCore;
  snapshot: ScenarioRuntimeSnapshot;
  fieldsById: Map<string, ScenarioInputField>;
};

type Renderer = (node: ScenarioLayoutNode, context: RenderContext) => ReactNode;

type RenderRegistry = Record<ScenarioLayoutNode["kind"], Renderer>;

type NodeInteractionProps = {
  onClick?: MouseEventHandler<HTMLElement>;
  onKeyDown?: KeyboardEventHandler<HTMLElement>;
  onDragStart?: DragEventHandler<HTMLElement>;
  onDragOver?: DragEventHandler<HTMLElement>;
  onDrop?: DragEventHandler<HTMLElement>;
  tabIndex?: number;
  draggable?: boolean;
};

function formatMetricValue(
  value: unknown,
  format: "percent" | "usd" | "number" | "text" | undefined,
  fallback: string | undefined,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return fallback ?? "n/a";
  }

  if (!format || format === "text") {
    return String(value);
  }

  if (typeof value !== "number") {
    return String(value);
  }

  if (format === "percent") {
    return `${value.toFixed(2)}%`;
  }
  if (format === "usd") {
    return `$${value.toFixed(2)}`;
  }
  return value.toLocaleString();
}

function resolveTemplateText(text: string, snapshot: ScenarioRuntimeSnapshot): string {
  const resolved = resolveValue(
    { template: text },
    {
      snapshot,
      event: {
        name: "__render__",
        payload: {},
        at: new Date().toISOString(),
      },
    },
  );
  return String(resolved ?? "");
}

function toRecordList(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

function disabledByCondition(
  button: ScenarioActionButton,
  snapshot: ScenarioRuntimeSnapshot,
): boolean {
  if (!button.disabledWhen) {
    return false;
  }
  return evaluateCondition(button.disabledWhen, {
    snapshot,
    event: {
      name: "__render__",
      payload: {},
      at: new Date().toISOString(),
    },
  });
}

function buildNodeInteractionProps(
  node: ScenarioLayoutNode,
  context: RenderContext,
): NodeInteractionProps {
  const source = node.interactionSource ?? node.id;
  const hasClick = context.engine.hasInteractionByTypeAndSource("click", source);
  const hasKeyboard = context.engine.hasInteractionByTypeAndSource("keyboard", source);
  const hasDrag = context.engine.hasInteractionByTypeAndSource("drag", source);

  if (!hasClick && !hasKeyboard && !hasDrag) {
    return {};
  }

  const trigger = (type: "click" | "keyboard" | "drag", payload: Record<string, unknown>) => {
    void context.engine.triggerInteractionByTypeAndSource(type, source, {
      nodeId: node.id,
      source,
      ...payload,
    });
  };

  const props: NodeInteractionProps = {};

  if (hasClick) {
    props.onClick = () => {
      trigger("click", {});
    };
  }

  if (hasKeyboard) {
    props.tabIndex = node.keyboardFocusable === false ? undefined : 0;
    props.onKeyDown = (event) => {
      trigger("keyboard", {
        key: event.key,
        code: event.code,
        repeat: event.repeat,
        altKey: event.altKey,
        ctrlKey: event.ctrlKey,
        metaKey: event.metaKey,
        shiftKey: event.shiftKey,
      });
    };
  }

  if (hasDrag) {
    props.draggable = node.draggable ?? true;
    props.onDragStart = (event) => {
      trigger("drag", {
        phase: "start",
        x: event.clientX,
        y: event.clientY,
      });
    };
    props.onDragOver = (event) => {
      event.preventDefault();
    };
    props.onDrop = (event) => {
      event.preventDefault();
      trigger("drag", {
        phase: "drop",
        x: event.clientX,
        y: event.clientY,
      });
    };
  }

  return props;
}

function renderChild(node: ScenarioLayoutNode, context: RenderContext, registry: RenderRegistry): ReactNode {
  const conditionResult = evaluateCondition(node.visibleWhen, {
    snapshot: context.snapshot,
    event: {
      name: "__render__",
      payload: {},
      at: new Date().toISOString(),
    },
  });
  if (!conditionResult) {
    return null;
  }

  const gateMessage = context.engine.getPermissionMessage(node.gateId);
  if (gateMessage) {
    return (
      <article key={node.id} className="pv-card p-4">
        <p className="text-sm font-semibold text-zinc-900">Locked for current plan</p>
        <p className="mt-1 text-sm text-zinc-600">{gateMessage}</p>
      </article>
    );
  }

  return registry[node.kind](node, context);
}

function buildRegistry(): RenderRegistry {
  const registry = {} as RenderRegistry;

  registry.container = (node, context) => {
    if (node.kind !== "container") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const className = node.direction === "grid" ? "grid gap-3" : "space-y-3";
    const style =
      node.direction === "grid"
        ? { gridTemplateColumns: `repeat(${Math.max(1, node.columns ?? 2)}, minmax(0, 1fr))` }
        : undefined;

    return (
      <div key={node.id} className={className} style={style} {...interactionProps}>
        {node.children.map((child) => renderChild(child, context, registry))}
      </div>
    );
  };

  registry.section = (node, context) => {
    if (node.kind !== "section") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const title = node.title ? resolveTemplateText(node.title, context.snapshot) : "";
    const subtitle = node.subtitle ? resolveTemplateText(node.subtitle, context.snapshot) : "";
    return (
      <section key={node.id} className="pv-panel px-6 py-6 sm:px-7" {...interactionProps}>
        {title ? <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2> : null}
        {subtitle ? <p className="mt-2 text-sm text-zinc-600">{subtitle}</p> : null}
        <div className="mt-5 space-y-3">{node.children.map((child) => renderChild(child, context, registry))}</div>
      </section>
    );
  };

  registry.hero = (node, context) => {
    if (node.kind !== "hero") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const title = resolveTemplateText(node.title, context.snapshot);
    const subtitle = node.subtitle ? resolveTemplateText(node.subtitle, context.snapshot) : "";
    const meta = node.meta ? resolveTemplateText(node.meta, context.snapshot) : "";
    return (
      <section key={node.id} className="pv-hero px-6 py-7 sm:px-8 sm:py-8" {...interactionProps}>
        {node.kicker ? <p className="pv-kicker">{node.kicker}</p> : null}
        <h1 className="pv-title max-w-4xl text-zinc-950">{title}</h1>
        {subtitle ? <p className="mt-3 pv-lead max-w-3xl">{subtitle}</p> : null}
        {meta ? <p className="mt-3 text-sm font-medium text-zinc-600">{meta}</p> : null}
        {node.tabs?.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {node.tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className="pv-nav-pill !min-h-0 !px-3 !py-1.5 !text-xs"
                onClick={() => {
                  if (!tab.interactionId) {
                    return;
                  }
                  void context.engine.triggerInteraction(tab.interactionId, { tab: tab.id });
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        ) : null}
      </section>
    );
  };

  registry.text = (node, context) => {
    if (node.kind !== "text") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const text = resolveTemplateText(node.text, context.snapshot);
    if (!text.trim()) {
      return null;
    }
    const toneClass =
      node.tone === "success"
        ? "text-emerald-700"
        : node.tone === "warning"
          ? "text-amber-700"
          : node.tone === "danger"
            ? "text-rose-700"
            : "text-zinc-600";
    return (
      <p key={node.id} className={`text-sm ${toneClass}`} {...interactionProps}>
        {text}
      </p>
    );
  };

  registry.actions = (node, context) => {
    if (node.kind !== "actions") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    return (
      <div key={node.id} className="flex flex-wrap gap-2" {...interactionProps}>
        {node.actions.map((action) => {
          const isDisabled = disabledByCondition(action, context.snapshot);
          return (
            <button
              key={action.id}
              type="button"
              className={action.tone === "primary" ? "pv-button-primary !w-auto" : "pv-button-secondary !w-auto"}
              disabled={isDisabled}
              onClick={() => void context.engine.triggerInteraction(action.interactionId, { actionId: action.id })}
            >
              {action.label}
            </button>
          );
        })}
      </div>
    );
  };

  registry.metric_grid = (node, context) => {
    if (node.kind !== "metric_grid") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const columns = Math.max(1, Math.min(8, node.columns ?? 4));
    return (
      <div
        key={node.id}
        className="grid gap-3"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
        {...interactionProps}
      >
        {node.items.map((item) => {
          const value = resolveValue(item.value, {
            snapshot: context.snapshot,
            event: {
              name: "__render__",
              payload: {},
              at: new Date().toISOString(),
            },
          });
          return (
            <article key={item.id} className="pv-analytics-card">
              <p className="pv-analytics-label">{item.label}</p>
              <p className="pv-analytics-value">{formatMetricValue(value, item.format, item.fallback)}</p>
            </article>
          );
        })}
      </div>
    );
  };

  registry.card_list = (node, context) => {
    if (node.kind !== "card_list") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const rows = toRecordList(getByPath(context.snapshot, node.source));
    const columns = Math.max(1, Math.min(4, node.columns ?? 2));

    const title = node.title ? resolveTemplateText(node.title, context.snapshot) : "";
    const subtitle = node.subtitle ? resolveTemplateText(node.subtitle, context.snapshot) : "";
    return (
      <div key={node.id} className="space-y-3" {...interactionProps}>
        {title ? <h3 className="text-lg font-semibold text-zinc-950">{title}</h3> : null}
        {subtitle ? <p className="text-sm text-zinc-600">{subtitle}</p> : null}
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
          {rows.length ? (
            rows.map((row, index) => (
              <article key={`${node.id}:${index}`} className="pv-analytics-card">
                {node.titleField ? <p className="text-sm font-semibold text-zinc-900">{String(row[node.titleField] ?? "n/a")}</p> : null}
                {node.subtitleField ? <p className="mt-1 text-xs text-zinc-600">{String(row[node.subtitleField] ?? "")}</p> : null}
                <div className="mt-2 space-y-1">
                  {node.fields.map((field) => (
                    <p key={`${node.id}:${index}:${field.key}`} className="pv-analytics-meta">
                      {field.label ? `${field.label}: ` : ""}
                      {formatMetricValue(row[field.key], field.format, field.fallback)}
                    </p>
                  ))}
                </div>
              </article>
            ))
          ) : (
            <article className="pv-analytics-card md:col-span-2">
              <p className="text-sm text-zinc-600">{node.emptyText ?? "No rows available."}</p>
            </article>
          )}
        </div>
      </div>
    );
  };

  registry.table = (node, context) => {
    if (node.kind !== "table") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const rows = toRecordList(getByPath(context.snapshot, node.source));
    const title = node.title ? resolveTemplateText(node.title, context.snapshot) : "";
    const subtitle = node.subtitle ? resolveTemplateText(node.subtitle, context.snapshot) : "";
    return (
      <div key={node.id} className="space-y-3" {...interactionProps}>
        {title ? <h3 className="text-lg font-semibold text-zinc-950">{title}</h3> : null}
        {subtitle ? <p className="text-sm text-zinc-600">{subtitle}</p> : null}
        <div className="pv-analytics-table-wrap">
          <table className="pv-analytics-table">
            <thead>
              <tr>
                {node.columns.map((column) => (
                  <th key={`${node.id}:head:${column.key}`}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((row, index) => (
                  <tr key={`${node.id}:row:${index}`}>
                    {node.columns.map((column) => (
                      <td key={`${node.id}:row:${index}:${column.key}`}>
                        {formatMetricValue(row[column.key], column.format, column.fallback)}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="pv-analytics-table-empty" colSpan={node.columns.length}>
                    {node.emptyText ?? "No rows available."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  registry.form = (node, context) => {
    if (node.kind !== "form") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);

    const fields = node.fieldIds
      .map((fieldId) => context.fieldsById.get(fieldId))
      .filter((field): field is ScenarioInputField => Boolean(field));

    const title = node.title ? resolveTemplateText(node.title, context.snapshot) : "";
    const subtitle = node.subtitle ? resolveTemplateText(node.subtitle, context.snapshot) : "";
    return (
      <form
        key={node.id}
        className="pv-analytics-form-grid"
        {...interactionProps}
        onSubmit={(event) => {
          event.preventDefault();
          void context.engine.triggerInteraction(node.submitInteractionId, { formId: node.formId });
        }}
      >
        {title ? <h3 className="sm:col-span-2 xl:col-span-3 text-lg font-semibold text-zinc-950">{title}</h3> : null}
        {subtitle ? <p className="sm:col-span-2 xl:col-span-3 text-sm text-zinc-600">{subtitle}</p> : null}
        {fields.map((field) => {
          const value = getByPath(context.snapshot, field.bind);
          const commonProps = {
            id: field.id,
            className: "pv-input",
            required: field.required ?? false,
          };

          if (field.type === "textarea") {
            return (
              <div key={field.id} className="pv-field sm:col-span-2 xl:col-span-3">
                <label className="pv-label" htmlFor={field.id}>
                  {field.label}
                </label>
                <textarea
                  {...commonProps}
                  placeholder={field.placeholder}
                  value={typeof value === "string" ? value : ""}
                  onChange={(event) =>
                    void context.engine.triggerInteraction(field.interactionId, {
                      fieldId: field.id,
                      bind: field.bind,
                      value: event.target.value,
                    })
                  }
                />
              </div>
            );
          }

          if (field.type === "select") {
            return (
              <div key={field.id} className="pv-field">
                <label className="pv-label" htmlFor={field.id}>
                  {field.label}
                </label>
                <select
                  {...commonProps}
                  value={typeof value === "string" ? value : ""}
                  onChange={(event) =>
                    void context.engine.triggerInteraction(field.interactionId, {
                      fieldId: field.id,
                      bind: field.bind,
                      value: event.target.value,
                    })
                  }
                >
                  {(field.options ?? []).map((option) => (
                    <option key={`${field.id}:${option.value}`} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            );
          }

          if (field.type === "checkbox") {
            const checked = Boolean(value);
            return (
              <div key={field.id} className="pv-field">
                <label className="pv-label" htmlFor={field.id}>
                  {field.label}
                </label>
                <input
                  id={field.id}
                  type="checkbox"
                  checked={checked}
                  onChange={(event) =>
                    void context.engine.triggerInteraction(field.interactionId, {
                      fieldId: field.id,
                      bind: field.bind,
                      value: event.target.checked,
                    })
                  }
                />
              </div>
            );
          }

          return (
            <div key={field.id} className="pv-field">
              <label className="pv-label" htmlFor={field.id}>
                {field.label}
              </label>
              <input
                {...commonProps}
                type={field.type}
                placeholder={field.placeholder}
                min={field.min}
                step={field.step}
                inputMode={field.inputMode}
                value={value === null || value === undefined ? "" : String(value)}
                onChange={(event) =>
                  void context.engine.triggerInteraction(field.interactionId, {
                    fieldId: field.id,
                    bind: field.bind,
                    value: event.target.value,
                  })
                }
              />
            </div>
          );
        })}
        <div className="sm:col-span-2 xl:col-span-3">
          <button type="submit" className="pv-button-primary !w-auto">
            {node.submitLabel}
          </button>
        </div>
      </form>
    );
  };

  registry.stream = (node, context) => {
    if (node.kind !== "stream") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const stream = getByPath(context.snapshot, node.source);
    const lines = Array.isArray(stream) ? stream.map((item) => String(item)) : [];
    const maxLines = node.maxLines ?? lines.length;
    const visible = lines.slice(-maxLines);

    return (
      <article key={node.id} className="pv-card p-4" {...interactionProps}>
        {visible.length ? (
          <pre className="max-h-[16rem] overflow-auto rounded-[0.75rem] border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-700 whitespace-pre-wrap">
            {visible.join("\n")}
          </pre>
        ) : (
          <p className="text-sm text-zinc-600">{node.emptyText ?? "No stream output yet."}</p>
        )}
      </article>
    );
  };

  registry.canvas = (node, context) => {
    if (node.kind !== "canvas") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    const dataset = getByPath(context.snapshot, node.source);
    return (
      <div key={node.id} {...interactionProps}>
        <CanvasPanel data={dataset} chart={node.chart} width={node.width} height={node.height} />
      </div>
    );
  };

  registry.hybrid = (node, context) => {
    if (node.kind !== "hybrid") {
      return null;
    }
    const interactionProps = buildNodeInteractionProps(node, context);
    return (
      <section key={node.id} className="space-y-3" {...interactionProps}>
        {node.children.map((child) => renderChild(child, context, registry))}
      </section>
    );
  };

  return registry;
}

function extractNumericSeries(data: unknown): number[] {
  if (Array.isArray(data) && data.every((item) => typeof item === "number")) {
    return data as number[];
  }
  if (Array.isArray(data)) {
    const rows = data as Array<Record<string, unknown>>;
    return rows
      .map((row) => {
        const numericEntry = Object.values(row).find((value) => typeof value === "number");
        return typeof numericEntry === "number" ? numericEntry : null;
      })
      .filter((value): value is number => value !== null);
  }
  return [];
}

function CanvasPanel({
  data,
  chart,
  width = 920,
  height = 180,
}: {
  data: unknown;
  chart: "bars" | "line" | "dots";
  width?: number;
  height?: number;
}) {
  const values = useMemo(() => extractNumericSeries(data), [data]);
  const svgWidth = width;
  const svgHeight = height;
  const max = Math.max(1, ...values);

  if (!values.length) {
    return (
      <article className="pv-card p-4">
        <p className="text-sm text-zinc-600">No canvas data to render yet.</p>
      </article>
    );
  }

  if (chart === "bars") {
    const gap = 8;
    const barWidth = (svgWidth - gap * (values.length + 1)) / values.length;
    return (
      <article className="pv-card p-4 overflow-auto">
        <svg width={svgWidth} height={svgHeight} role="img" aria-label="Scenario canvas bars">
          {values.map((value, index) => {
            const normalized = value / max;
            const barHeight = normalized * (svgHeight - 20);
            const x = gap + index * (barWidth + gap);
            const y = svgHeight - barHeight - 8;
            return (
              <rect
                key={`bar-${index}`}
                x={x}
                y={y}
                width={Math.max(3, barWidth)}
                height={barHeight}
                rx={3}
                fill="#2563eb"
                opacity={0.82}
              />
            );
          })}
        </svg>
      </article>
    );
  }

  if (chart === "dots") {
    const step = values.length > 1 ? svgWidth / (values.length - 1) : svgWidth / 2;
    return (
      <article className="pv-card p-4 overflow-auto">
        <svg width={svgWidth} height={svgHeight} role="img" aria-label="Scenario canvas dots">
          {values.map((value, index) => {
            const x = index * step;
            const y = svgHeight - (value / max) * (svgHeight - 20) - 8;
            return <circle key={`dot-${index}`} cx={x} cy={y} r={4} fill="#16a34a" />;
          })}
        </svg>
      </article>
    );
  }

  const step = values.length > 1 ? svgWidth / (values.length - 1) : svgWidth / 2;
  const path = values
    .map((value, index) => {
      const x = index * step;
      const y = svgHeight - (value / max) * (svgHeight - 20) - 8;
      return `${index === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  return (
    <article className="pv-card p-4 overflow-auto">
      <svg width={svgWidth} height={svgHeight} role="img" aria-label="Scenario canvas line">
        <path d={path} fill="none" stroke="#0ea5e9" strokeWidth={2} />
      </svg>
    </article>
  );
}

export class RenderEngine {
  private readonly registry: RenderRegistry;

  constructor(registry?: Partial<RenderRegistry>) {
    this.registry = {
      ...buildRegistry(),
      ...(registry ?? {}),
    } as RenderRegistry;
  }

  render(nodes: ScenarioLayoutNode[], context: RenderContext): ReactNode {
    return nodes.map((node) => renderChild(node, context, this.registry));
  }
}
