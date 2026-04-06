import type { ScenarioDefinition } from "../../types";

const SHOW_WHEN_ERROR = { path: "state.ui.error", exists: true } as const;
const SHOW_WHEN_READY = { not: SHOW_WHEN_ERROR } as const;

export const growthOpsScenario: ScenarioDefinition = {
  id: "ops-growth-dashboard",
  type: "tool",
  version: 3,
  title: "Growth Operating Dashboard",
  description: "Activation, retention, and experiment analytics as a generated mini-app.",
  layout: {
    panels: [
      {
        id: "growth-hero",
        kind: "hero",
        renderer: "dom",
        kicker: "Growth OS",
        title: "Growth Operating Dashboard",
        subtitle: "Activation, retention, and upgrade conversion for the active window.",
        meta: "Window: {{state.global.dashboard.metrics.window_days}}d · Updated: {{state.global.dashboard.metrics.computed_at}}",
        tabs: [
          { id: "growth", label: "Growth", interactionId: "growth.tab.growth" },
          { id: "revenue", label: "Revenue", interactionId: "growth.tab.revenue" },
          { id: "gtm", label: "GTM", interactionId: "growth.tab.gtm" },
        ],
      },
      {
        id: "growth-actions",
        kind: "section",
        renderer: "dom",
        children: [
          {
            id: "growth-action-row",
            kind: "actions",
            renderer: "dom",
            actions: [
              {
                id: "growth-refresh",
                label: "Refresh dashboard",
                tone: "primary",
                interactionId: "growth.refresh",
              },
            ],
          },
          {
            id: "growth-status-message",
            kind: "text",
            renderer: "dom",
            text: "{{state.ui.status_message}}",
            tone: "success",
          },
        ],
      },
      {
        id: "growth-error-section",
        kind: "section",
        renderer: "dom",
        title: "Growth dashboard is unavailable",
        subtitle: "Generate loop events and refresh this app.",
        visibleWhen: SHOW_WHEN_ERROR,
        children: [
          {
            id: "growth-error-message",
            kind: "text",
            renderer: "dom",
            text: "{{state.ui.error}}",
            tone: "danger",
          },
          {
            id: "growth-empty-steps",
            kind: "card_list",
            renderer: "dom",
            source: "global.empty_steps",
            emptyText: "No setup steps available.",
            titleField: "label",
            subtitleField: "body",
            fields: [],
            columns: 3,
          },
          {
            id: "growth-empty-actions",
            kind: "actions",
            renderer: "dom",
            actions: [
              { id: "growth-empty-retry", label: "Retry", tone: "primary", interactionId: "growth.refresh" },
            ],
          },
        ],
      },
      {
        id: "growth-metrics-section",
        kind: "section",
        renderer: "dom",
        title: "Core metrics",
        subtitle: "Activation and retention pulse for the product loop.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "growth-metrics-grid",
            kind: "metric_grid",
            renderer: "dom",
            columns: 6,
            items: [
              {
                id: "growth-activation",
                label: "Activation",
                value: { from: "state.global.dashboard.metrics.activation_rate" },
                format: "percent",
              },
              {
                id: "growth-d1",
                label: "D1 retention",
                value: { from: "state.global.dashboard.metrics.d1_retention" },
                format: "percent",
              },
              {
                id: "growth-d7",
                label: "D7 retention",
                value: { from: "state.global.dashboard.metrics.d7_retention" },
                format: "percent",
              },
              {
                id: "growth-conversion",
                label: "Free → Paid",
                value: { from: "state.global.dashboard.metrics.free_to_paid_conversion" },
                format: "percent",
              },
              {
                id: "growth-upgrade",
                label: "Upgrade intent",
                value: { from: "state.global.dashboard.metrics.upgrade_intent_rate" },
                format: "percent",
              },
              {
                id: "growth-ltv",
                label: "LTV proxy",
                value: { from: "state.global.dashboard.metrics.ltv_proxy_usd" },
                format: "usd",
              },
            ],
          },
        ],
      },
      {
        id: "growth-funnel-section",
        kind: "section",
        renderer: "dom",
        title: "Funnel",
        subtitle: "Find drop-offs before paid conversion.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "growth-funnel-cards",
            kind: "card_list",
            renderer: "dom",
            source: "global.dashboard.funnel.steps",
            emptyText: "No funnel data available.",
            titleField: "label",
            fields: [
              { key: "users", label: "Users", format: "number" },
              { key: "conversion_from_prev", label: "Conv from prev", format: "percent" },
            ],
            columns: 5,
          },
          {
            id: "growth-funnel-canvas",
            kind: "canvas",
            renderer: "canvas",
            source: "global.dashboard.funnel.steps",
            chart: "bars",
            height: 180,
          },
        ],
      },
      {
        id: "growth-cohort-section",
        kind: "section",
        renderer: "dom",
        title: "Cohorts",
        subtitle: "Weekly retention and paid conversion benchmark.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "growth-cohort-table",
            kind: "table",
            renderer: "dom",
            source: "global.dashboard.cohorts",
            emptyText: "No cohort rows in the selected window.",
            columns: [
              { key: "cohort_week_start", label: "Week", format: "text" },
              { key: "users", label: "Users", format: "number" },
              { key: "d1_retention", label: "D1", format: "percent" },
              { key: "d7_retention", label: "D7", format: "percent" },
              { key: "paid_30d_conversion", label: "Paid 30d", format: "percent" },
            ],
          },
        ],
      },
      {
        id: "growth-experiment-section",
        kind: "section",
        renderer: "dom",
        gateId: "advanced_insights",
        title: "Experiment performance",
        subtitle: "Conversion and D7 retention by active experiments.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "growth-experiment-table",
            kind: "table",
            renderer: "dom",
            source: "global.derived.experiment_rows",
            emptyText: "No experiment data captured yet.",
            columns: [
              { key: "experiment", label: "Experiment", format: "text" },
              { key: "variant", label: "Variant", format: "text" },
              { key: "users", label: "Users", format: "number" },
              { key: "conversion", label: "Conversion", format: "percent" },
              { key: "retention_d7", label: "D7 retention", format: "percent" },
            ],
          },
        ],
      },
      {
        id: "growth-flags-section",
        kind: "section",
        renderer: "dom",
        title: "Rollout flags",
        subtitle: "Current flag rollout configuration and eligibility target.",
        visibleWhen: SHOW_WHEN_READY,
        children: [
          {
            id: "growth-flags-cards",
            kind: "card_list",
            renderer: "dom",
            source: "global.dashboard.rollout_flags",
            emptyText: "No rollout flags configured.",
            titleField: "key",
            subtitleField: "target",
            fields: [
              { key: "rollout_percent", label: "Rollout %", format: "number" },
              { key: "enabled", label: "Enabled", format: "text" },
              { key: "reason", label: "Reason", format: "text" },
            ],
            columns: 3,
          },
        ],
      },
      {
        id: "growth-stream-section",
        kind: "section",
        renderer: "dom",
        title: "Runtime stream",
        subtitle: "Event-driven updates from the scenario engine.",
        children: [
          {
            id: "growth-stream",
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
    interactions: [
      { id: "growth.refresh", type: "click", source: "growth.refresh", emits: "app/refresh" },
      {
        id: "growth.tab.growth",
        type: "click",
        source: "growth.tab.growth",
        emits: "ops/tab-selected",
        payload: { tab: "growth" },
      },
      {
        id: "growth.tab.revenue",
        type: "click",
        source: "growth.tab.revenue",
        emits: "ops/tab-selected",
        payload: { tab: "revenue" },
      },
      {
        id: "growth.tab.gtm",
        type: "click",
        source: "growth.tab.gtm",
        emits: "ops/tab-selected",
        payload: { tab: "gtm" },
      },
    ],
  },
  logic: {
    entryEvents: ["app/init"],
    steps: [
      {
        id: "growth-init",
        on: "app/init",
        actions: [
          { kind: "set", target: "ui.loading", value: true },
          { kind: "clear", target: "ui.error" },
          {
            kind: "invoke",
            actionId: "analytics.fetchGrowthDashboard",
            input: {
              window_days: { from: "state.local.filters.window_days", fallback: 28 },
            },
            assign: "global.dashboard",
            onErrorAssign: "ui.error",
          },
          {
            kind: "invoke",
            actionId: "analytics.flattenGrowthExperimentRows",
            input: {
              dashboard: { from: "state.global.dashboard" },
            },
            assign: "global.derived.experiment_rows",
          },
          {
            kind: "append",
            target: "streams.activity",
            value: { template: "{{event.at}} · growth dashboard loaded" },
          },
          { kind: "set", target: "ui.status_message", value: "Growth runtime synced." },
          { kind: "set", target: "ui.loading", value: false },
          { kind: "persist", scope: "local" },
        ],
      },
      {
        id: "growth-refresh-limit",
        on: "app/refresh",
        actions: [
          {
            kind: "check_limit",
            limitId: "growth_refresh",
            ifExceededEvent: "growth/refresh-limit-exceeded",
          },
          { kind: "emit", event: "app/init" },
        ],
      },
      {
        id: "growth-refresh-limit-reached",
        on: "growth/refresh-limit-exceeded",
        actions: [
          {
            kind: "set",
            target: "ui.status_message",
            value: "Refresh limit reached for free usage window.",
          },
          {
            kind: "append",
            target: "streams.activity",
            value: { template: "{{event.at}} · refresh cap reached" },
          },
        ],
      },
      {
        id: "growth-tab-selected",
        on: "ops/tab-selected",
        actions: [
          { kind: "set", target: "ui.active_tab", value: { from: "event.payload.tab" } },
          {
            kind: "append",
            target: "streams.activity",
            value: { template: "{{event.at}} · active tab {{event.payload.tab}}" },
          },
        ],
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
      { scope: "global", key: "derived.experiment_rows", initial: [] },
      {
        scope: "global",
        key: "empty_steps",
        initial: [
          { label: "1. Run scenarios", body: "Generate activity from workbench or catalog flows." },
          { label: "2. Activate billing", body: "Enable plan tracking to unlock conversion metrics." },
          { label: "3. Re-open dashboard", body: "Refresh this app after ingestion completes." },
        ],
      },
      { scope: "local", key: "filters.window_days", initial: 28 },
      { scope: "ui", key: "loading", initial: true },
      { scope: "ui", key: "error", initial: null },
      { scope: "ui", key: "status_message", initial: "" },
      { scope: "ui", key: "active_tab", initial: "growth" },
      { scope: "streams", key: "activity", initial: [] },
    ],
    persistence: {
      key: "ops-growth-dashboard-v3",
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
        id: "advanced_insights",
        requires: "pro",
        message: "PRO unlocks advanced experiment insights and full diagnostics.",
      },
    ],
    usageLimits: [
      {
        id: "growth_refresh",
        event: "app/refresh",
        max: 30,
        window: "session",
      },
    ],
  },
  composition: {
    pipeline: ["ops-growth-dashboard", "ops-revenue-dashboard", "ops-gtm-dashboard"],
    sharedState: [
      { from: "global.dashboard.metrics.activation_rate", to: "global.shared.activation_rate" },
    ],
  },
  sandbox: {
    allowedActions: [
      "analytics.fetchGrowthDashboard",
      "analytics.flattenGrowthExperimentRows",
      "runtime.noop",
    ],
    maxActionMs: 6000,
    maxEventsPerMinute: 240,
  },
};
