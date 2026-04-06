import type { ScenarioDefinition } from "../../types";

const SHOW_WHEN_ERROR = { path: "state.ui.error", exists: true } as const;
const SHOW_WHEN_READY = { not: SHOW_WHEN_ERROR } as const;

export const revenueOpsScenario: ScenarioDefinition = {
  id: "ops-revenue-dashboard",
  type: "tool",
  version: 3,
  title: "Revenue OS Dashboard",
  description: "MRR health, conversion quality, and monetization efficiency.",
  layout: {
    panels: [
      {
        id: "revenue-hero",
        kind: "hero",
        renderer: "dom",
        kicker: "Revenue OS",
        title: "Revenue OS Dashboard",
        subtitle: "MRR health, conversion quality, and monetization efficiency.",
        meta: "Window: {{state.global.dashboard.headline.window_days}}d · Updated: {{state.global.dashboard.headline.computed_at}}",
      },
      {
        id: "revenue-actions",
        kind: "section",
        renderer: "dom",
        children: [
          {
            id: "revenue-action-row",
            kind: "actions",
            renderer: "dom",
            actions: [
              {
                id: "revenue-refresh",
                label: "Refresh dashboard",
                tone: "primary",
                interactionId: "revenue.refresh",
              },
            ],
          },
          {
            id: "revenue-status",
            kind: "text",
            renderer: "dom",
            text: "{{state.ui.status_message}}",
            tone: "success",
          },
        ],
      },
      {
        id: "revenue-error",
        kind: "section",
        renderer: "dom",
        title: "Revenue dashboard is unavailable",
        subtitle: "Start billing and rerun analytics ingestion.",
        visibleWhen: SHOW_WHEN_ERROR,
        children: [
          {
            id: "revenue-error-message",
            kind: "text",
            renderer: "dom",
            text: "{{state.ui.error}}",
            tone: "danger",
          },
        ],
      },
      {
        id: "revenue-metrics",
        kind: "section",
        renderer: "dom",
        title: "Revenue pulse",
        subtitle: "Topline subscription and monetization metrics.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-metric-grid",
            kind: "metric_grid",
            renderer: "dom",
            columns: 8,
            items: [
              { id: "mrr", label: "MRR", value: { from: "state.global.dashboard.headline.mrr_usd" }, format: "usd" },
              { id: "arr", label: "ARR", value: { from: "state.global.dashboard.headline.arr_usd" }, format: "usd" },
              { id: "arpu", label: "ARPU", value: { from: "state.global.dashboard.headline.arpu_usd" }, format: "usd" },
              {
                id: "free-paid",
                label: "Free → Paid",
                value: { from: "state.global.dashboard.headline.free_to_paid_conversion" },
                format: "percent",
              },
              {
                id: "rpu",
                label: "Revenue / Active User",
                value: { from: "state.global.dashboard.headline.revenue_per_user_usd" },
                format: "usd",
              },
              {
                id: "churn",
                label: "Churn",
                value: { from: "state.global.dashboard.headline.churn_rate" },
                format: "percent",
              },
              {
                id: "ltv",
                label: "LTV proxy",
                value: { from: "state.global.dashboard.headline.ltv_proxy_usd" },
                format: "usd",
              },
              {
                id: "retention",
                label: "Paying D30 retention",
                value: { from: "state.global.dashboard.headline.paying_user_retention_d30" },
                format: "percent",
              },
            ],
          },
        ],
      },
      {
        id: "revenue-funnel-section",
        kind: "section",
        renderer: "dom",
        title: "Revenue funnel",
        subtitle: "Full path from acquisition to paid conversion.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-funnel-cards",
            kind: "card_list",
            renderer: "dom",
            source: "global.dashboard.funnel.steps",
            emptyText: "No funnel rows available.",
            titleField: "label",
            fields: [
              { key: "users", label: "Users", format: "number" },
              { key: "conversion_from_prev", label: "Conv", format: "percent" },
            ],
            columns: 4,
          },
          {
            id: "revenue-funnel-canvas",
            kind: "canvas",
            renderer: "canvas",
            source: "global.dashboard.funnel.steps",
            chart: "line",
            height: 180,
          },
        ],
      },
      {
        id: "revenue-by-source",
        kind: "section",
        renderer: "dom",
        title: "Revenue by source",
        subtitle: "MRR and conversion contribution per acquisition source.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-by-source-table",
            kind: "table",
            renderer: "dom",
            source: "global.dashboard.revenue_by_source",
            emptyText: "No source-attributed revenue in this window.",
            columns: [
              { key: "source", label: "Source", format: "text" },
              { key: "acquired_users", label: "Acquired", format: "number" },
              { key: "paid_users", label: "Paid", format: "number" },
              { key: "conversion_rate", label: "Conversion", format: "percent" },
              { key: "mrr_usd", label: "MRR", format: "usd" },
            ],
          },
        ],
      },
      {
        id: "revenue-paywall",
        kind: "section",
        renderer: "dom",
        title: "Paywall performance",
        subtitle: "Performance by paywall and pricing variants.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-paywall-table",
            kind: "table",
            renderer: "dom",
            source: "global.dashboard.paywall_performance",
            emptyText: "No paywall experiments observed.",
            columns: [
              { key: "experiment_key", label: "Experiment", format: "text" },
              { key: "variant", label: "Variant", format: "text" },
              { key: "views", label: "Views", format: "number" },
              { key: "interactions", label: "Interactions", format: "number" },
              { key: "paid_users", label: "Paid", format: "number" },
              { key: "conversion_rate", label: "Conv", format: "percent" },
              { key: "revenue_per_user_usd", label: "RPU", format: "usd" },
            ],
          },
        ],
      },
      {
        id: "revenue-source-funnel",
        kind: "section",
        renderer: "dom",
        title: "Funnel by source",
        subtitle: "Contribution flow from acquisition to paid by source.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-source-funnel-table",
            kind: "table",
            renderer: "dom",
            source: "global.dashboard.funnel_by_source",
            emptyText: "No source funnel rows for this period.",
            columns: [
              { key: "source", label: "Source", format: "text" },
              { key: "acquired_users", label: "Acquired", format: "number" },
              { key: "paid_users", label: "Paid", format: "number" },
              { key: "conversion_rate", label: "Conv", format: "percent" },
              { key: "arr_usd", label: "ARR", format: "usd" },
            ],
          },
        ],
      },
      {
        id: "revenue-cohort-section",
        kind: "section",
        renderer: "dom",
        gateId: "cohort_depth",
        title: "Top cohorts",
        subtitle: "Revenue quality by signup week, source, and plan tier.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-cohort-table",
            kind: "table",
            renderer: "dom",
            source: "global.dashboard.cohorts",
            emptyText: "No cohort rows available.",
            columns: [
              { key: "cohort_week_start", label: "Week", format: "text" },
              { key: "source", label: "Source", format: "text" },
              { key: "plan_tier", label: "Plan", format: "text" },
              { key: "users", label: "Users", format: "number" },
              { key: "paid_users", label: "Paid", format: "number" },
              { key: "revenue_usd", label: "Revenue", format: "usd" },
              { key: "retention_d30", label: "D30 retention", format: "percent" },
              { key: "conversion_lag_days", label: "Conv lag", format: "number" },
            ],
          },
        ],
      },
      {
        id: "revenue-churn",
        kind: "section",
        renderer: "dom",
        title: "Churn signals",
        subtitle: "Risk counters for immediate retention actions.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "revenue-churn-metrics",
            kind: "metric_grid",
            renderer: "dom",
            columns: 3,
            items: [
              {
                id: "churn-risk",
                label: "At risk",
                value: { from: "state.global.dashboard.churn_signals.churn_risk_users" },
                format: "number",
              },
              {
                id: "churn-canceled",
                label: "Canceled",
                value: { from: "state.global.dashboard.churn_signals.canceled_users" },
                format: "number",
              },
              {
                id: "churn-inactive",
                label: "Inactive paying",
                value: { from: "state.global.dashboard.churn_signals.inactive_paying_users" },
                format: "number",
              },
            ],
          },
        ],
      },
      {
        id: "revenue-stream-section",
        kind: "section",
        renderer: "dom",
        title: "Runtime stream",
        subtitle: "Event-driven updates from revenue scenario runtime.",
        children: [
          {
            id: "revenue-stream",
            kind: "stream",
            renderer: "stream",
            source: "streams.activity",
            maxLines: 8,
            emptyText: "No runtime events yet.",
          },
        ],
      },
    ],
  },
  inputs: {
    fields: [],
    interactions: [{ id: "revenue.refresh", type: "click", source: "revenue.refresh", emits: "app/refresh" }],
  },
  logic: {
    entryEvents: ["app/init"],
    steps: [
      {
        id: "revenue-init",
        on: "app/init",
        actions: [
          { kind: "set", target: "ui.loading", value: true },
          { kind: "clear", target: "ui.error" },
          {
            kind: "invoke",
            actionId: "analytics.fetchRevenueDashboard",
            input: {
              window_days: { from: "state.local.filters.window_days", fallback: 30 },
            },
            assign: "global.dashboard",
            onErrorAssign: "ui.error",
          },
          {
            kind: "append",
            target: "streams.activity",
            value: { template: "{{event.at}} · revenue dashboard loaded" },
          },
          { kind: "set", target: "ui.status_message", value: "Revenue runtime synced." },
          { kind: "set", target: "ui.loading", value: false },
          { kind: "persist", scope: "local" },
        ],
      },
      {
        id: "revenue-refresh",
        on: "app/refresh",
        actions: [{ kind: "emit", event: "app/init" }],
      },
    ],
  },
  output: {
    renderer: "hybrid",
    liveUpdates: true,
    streamPath: "streams.activity",
  },
  state: {
    variables: [
      { scope: "global", key: "dashboard", initial: {} },
      { scope: "local", key: "filters.window_days", initial: 30 },
      { scope: "ui", key: "loading", initial: true },
      { scope: "ui", key: "error", initial: null },
      { scope: "ui", key: "status_message", initial: "" },
      { scope: "streams", key: "activity", initial: [] },
    ],
    persistence: {
      key: "ops-revenue-dashboard-v3",
      local: true,
      server: false,
      autosaveMs: 500,
    },
    enableUndoRedo: true,
    enableReplay: true,
    resumeEvent: "app/init",
  },
  permissions: {
    defaultTier: "free",
    gates: [
      {
        id: "cohort_depth",
        requires: "pro",
        message: "PRO unlocks deep cohort analytics and full conversion lag traces.",
      },
    ],
    usageLimits: [
      {
        id: "revenue_refresh",
        event: "app/refresh",
        max: 30,
        window: "session",
      },
    ],
  },
  composition: {
    pipeline: ["ops-growth-dashboard", "ops-revenue-dashboard"],
    sharedState: [{ from: "global.dashboard.headline.mrr_usd", to: "global.shared.mrr_usd" }],
  },
  sandbox: {
    allowedActions: ["analytics.fetchRevenueDashboard", "runtime.noop"],
    maxActionMs: 6000,
    maxEventsPerMinute: 240,
  },
};
