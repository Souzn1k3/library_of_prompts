import { mapPromptListToScenarios } from "@/features/scenarios/infrastructure/promptScenarioMapper";
import type {
  PromptListItem,
  ScenarioChainRead,
  ScenarioNextStepRead,
  ScenarioPackRead,
  ScenarioPricingPlanRead,
  ScenarioReturnTriggerRead,
  ScenarioShowcaseRead,
} from "@/lib/types";

import type { ScenarioDefinition } from "../../types";

export type HomeScenariosShowcaseLabels = {
  kicker: string;
  title: string;
  subtitle: string;
  openHub: string;
  labTitle: string;
  labPlaceholder: string;
  runNow: string;
  outputDetailed: string;
  outputConcise: string;
  openScenario: string;
  openWorkspace: string;
  packsTitle: string;
  chainsTitle: string;
  retentionTitle: string;
  nextStepsTitle: string;
  returnTitle: string;
  showcaseTitle: string;
  pricingTitle: string;
  pricingStudioAction: string;
  pricingMarketplaceAction: string;
  upgradeAction: string;
};

export type HomeScenariosShowcaseInput = {
  prompts: PromptListItem[];
  recommendedPrompts: PromptListItem[];
  retentionPrompts: PromptListItem[];
  packs: ScenarioPackRead[];
  chains: ScenarioChainRead[];
  nextSteps: ScenarioNextStepRead[];
  returnTriggers: ScenarioReturnTriggerRead[];
  showcase: ScenarioShowcaseRead[];
  pricingPlans: ScenarioPricingPlanRead[];
  isAuthenticated: boolean;
  language: "en" | "ru" | "tt";
  labels: HomeScenariosShowcaseLabels;
};

function dedupePrompts(prompts: PromptListItem[]): PromptListItem[] {
  const map = new Map<string, PromptListItem>();
  for (const prompt of prompts) {
    map.set(prompt.id, prompt);
  }
  return [...map.values()];
}

function toChainItems(
  chains: ScenarioChainRead[],
  fallbackScenarios: Array<{ id: string; title: string; summary: string }>,
): Array<{ id: string; title: string; summary: string }> {
  const chainSteps = chains.find((chain) => chain.steps.length >= 2)?.steps ?? [];
  if (chainSteps.length) {
    return chainSteps.map((step) => ({
      id: step.prompt_slug,
      title: step.title,
      summary: step.goal,
    }));
  }
  return fallbackScenarios.map((scenario) => ({
    id: scenario.id,
    title: scenario.title,
    summary: scenario.summary,
  }));
}

export function buildHomeScenariosShowcaseScenarioDefinition(
  input: HomeScenariosShowcaseInput,
): ScenarioDefinition {
  const featuredScenarios = mapPromptListToScenarios(
    dedupePrompts([...input.recommendedPrompts, ...input.prompts]).slice(0, 4),
  );
  const chainFallback = mapPromptListToScenarios(
    dedupePrompts([...input.retentionPrompts, ...input.prompts]).slice(0, 3),
  );
  const chainItems = toChainItems(
    input.chains,
    chainFallback.map((scenario) => ({
      id: scenario.id,
      title: scenario.title,
      summary: scenario.summary,
    })),
  );
  const totalSaveSignals = featuredScenarios.reduce((acc, scenario) => acc + scenario.saveCount, 0);
  const highQualityScenarios = featuredScenarios.filter((scenario) => scenario.qualityScore >= 70).length;
  const initialSlug = featuredScenarios[0]?.slug ?? "";
  const featuredOptions = featuredScenarios.map((scenario) => ({
    label: scenario.title,
    value: scenario.slug,
  }));

  return {
    id: "home-scenarios-showcase-runtime",
    type: "hybrid",
    version: 3,
    title: input.labels.title,
    description: input.labels.subtitle,
    layout: {
      panels: [
        {
          id: "showcase-hero",
          kind: "hero",
          renderer: "dom",
          kicker: input.labels.kicker,
          title: input.labels.title,
          subtitle: input.labels.subtitle,
        },
        {
          id: "showcase-entry-actions",
          kind: "section",
          renderer: "dom",
          children: [
            {
              id: "showcase-entry-action-row",
              kind: "actions",
              renderer: "dom",
              actions: [
                {
                  id: "showcase-open-hub",
                  label: input.labels.openHub,
                  tone: "primary",
                  interactionId: "showcase-open-hub",
                },
              ],
            },
          ],
        },
        {
          id: "showcase-featured",
          kind: "section",
          renderer: "dom",
          title: "Featured scenarios",
          subtitle: "Generated cards based on recommendation feed.",
          children: [
            {
              id: "showcase-featured-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.featured_scenarios",
              emptyText: "No featured scenarios available.",
              titleField: "title",
              subtitleField: "summary",
              fields: [
                { key: "category", label: "Category", format: "text" },
                { key: "qualityScore", label: "Quality", format: "number" },
                { key: "saveCount", label: "Saves", format: "number" },
              ],
              columns: 2,
            },
          ],
        },
        {
          id: "showcase-lab",
          kind: "section",
          renderer: "hybrid",
          title: input.labels.labTitle,
          subtitle: "Live preview rendered from DSL state and logic.",
          children: [
            {
              id: "showcase-lab-form",
              kind: "form",
              renderer: "dom",
              formId: "showcase_lab",
              fieldIds: ["showcase-selected-slug", "showcase-scenario-input"],
              submitLabel: input.labels.runNow,
              submitInteractionId: "showcase-run",
            },
            {
              id: "showcase-mode-actions",
              kind: "actions",
              renderer: "dom",
              actions: [
                {
                  id: "showcase-mode-detailed",
                  label: input.labels.outputDetailed,
                  tone: "secondary",
                  interactionId: "showcase-mode-detailed",
                },
                {
                  id: "showcase-mode-concise",
                  label: input.labels.outputConcise,
                  tone: "secondary",
                  interactionId: "showcase-mode-concise",
                },
                {
                  id: "showcase-open-selected",
                  label: input.labels.openScenario,
                  tone: "secondary",
                  interactionId: "showcase-open-selected",
                },
                {
                  id: "showcase-open-workspace",
                  label: input.labels.openWorkspace,
                  tone: "secondary",
                  interactionId: "showcase-open-workspace",
                },
                {
                  id: "showcase-upgrade",
                  label: input.labels.upgradeAction,
                  tone: "primary",
                  interactionId: "showcase-upgrade",
                },
              ],
            },
            {
              id: "showcase-guard-message",
              kind: "text",
              renderer: "dom",
              tone: "warning",
              text: "{{state.ui.guard_message}}",
              visibleWhen: { path: "state.ui.guard_message", exists: true },
            },
            {
              id: "showcase-live-output",
              kind: "stream",
              renderer: "stream",
              source: "streams.live_output",
              maxLines: 48,
              emptyText: "Run a scenario to generate live output.",
            },
          ],
        },
        {
          id: "showcase-packs",
          kind: "section",
          renderer: "dom",
          title: input.labels.packsTitle,
          subtitle: "Pack recommendations from scenario aggregate feed.",
          children: [
            {
              id: "showcase-packs-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.packs",
              emptyText: "No packs available.",
              titleField: "title",
              subtitleField: "description",
              fields: [
                { key: "outcome", label: "Outcome", format: "text" },
                { key: "id", label: "Pack ID", format: "text" },
              ],
              columns: 3,
            },
          ],
        },
        {
          id: "showcase-chain-retention",
          kind: "section",
          renderer: "dom",
          title: input.labels.chainsTitle,
          subtitle: "Scenario composition chain built from recommendations.",
          children: [
            {
              id: "showcase-chain-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.chain_items",
              emptyText: "No chain items available.",
              titleField: "title",
              subtitleField: "summary",
              fields: [],
              columns: 2,
            },
            {
              id: "showcase-retention-metrics",
              kind: "metric_grid",
              renderer: "dom",
              columns: 3,
              items: [
                {
                  id: "showcase-metric-scenarios",
                  label: "Featured scenarios",
                  value: { from: "state.global.metrics.featured_count" },
                  format: "number",
                },
                {
                  id: "showcase-metric-saves",
                  label: "Save signals",
                  value: { from: "state.global.metrics.total_saves" },
                  format: "number",
                },
                {
                  id: "showcase-metric-quality",
                  label: "High quality count",
                  value: { from: "state.global.metrics.high_quality" },
                  format: "number",
                },
              ],
            },
          ],
        },
        {
          id: "showcase-next-return",
          kind: "section",
          renderer: "dom",
          title: input.labels.nextStepsTitle,
          subtitle: input.labels.returnTitle,
          children: [
            {
              id: "showcase-next-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.next_steps",
              emptyText: "No next-step recommendations yet.",
              titleField: "next_prompt_slug",
              subtitleField: "reason",
              fields: [
                { key: "confidence", label: "Confidence", format: "number" },
              ],
              columns: 2,
            },
            {
              id: "showcase-return-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.return_triggers",
              emptyText: "No return triggers available.",
              titleField: "label",
              subtitleField: "href",
              fields: [
                { key: "count", label: "Count", format: "number" },
              ],
              columns: 2,
            },
          ],
        },
        {
          id: "showcase-showcase-pricing",
          kind: "section",
          renderer: "dom",
          title: input.labels.showcaseTitle,
          subtitle: input.labels.pricingTitle,
          children: [
            {
              id: "showcase-share-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.showcase",
              emptyText: "No showcase items yet.",
              titleField: "title",
              subtitleField: "excerpt",
              fields: [
                { key: "output_preview", label: "Preview", format: "text" },
                { key: "upvotes", label: "Upvotes", format: "number" },
              ],
              columns: 3,
            },
            {
              id: "showcase-pricing-cards",
              kind: "card_list",
              renderer: "dom",
              source: "global.pricing_plans",
              emptyText: "No pricing plans available.",
              titleField: "tier",
              subtitleField: "headline",
              fields: [
                { key: "price_monthly_usd", label: "Price", format: "usd" },
              ],
              columns: 4,
            },
            {
              id: "showcase-pricing-actions",
              kind: "actions",
              renderer: "dom",
              actions: [
                {
                  id: "showcase-open-studio",
                  label: input.labels.pricingStudioAction,
                  tone: "secondary",
                  interactionId: "showcase-open-studio",
                },
                {
                  id: "showcase-open-marketplace",
                  label: input.labels.pricingMarketplaceAction,
                  tone: "primary",
                  interactionId: "showcase-open-marketplace",
                },
              ],
            },
          ],
        },
      ],
    },
    inputs: {
      fields: [
        {
          id: "showcase-selected-slug",
          formId: "showcase_lab",
          label: "Scenario",
          type: "select",
          bind: "local.selected_slug",
          options: featuredOptions,
          interactionId: "showcase-selection-updated",
        },
        {
          id: "showcase-scenario-input",
          formId: "showcase_lab",
          label: input.labels.labPlaceholder,
          type: "textarea",
          bind: "local.scenario_input",
          placeholder: input.labels.labPlaceholder,
          interactionId: "showcase-input-updated",
        },
      ],
      interactions: [
        {
          id: "showcase-selection-updated",
          type: "input",
          source: "showcase-selected-slug",
          emits: "showcase/selection-updated",
          payload: {
            bind: { from: "interaction.bind" },
            value: { from: "interaction.value" },
          },
        },
        {
          id: "showcase-input-updated",
          type: "input",
          source: "showcase-scenario-input",
          emits: "form/update",
          payload: {
            bind: { from: "interaction.bind" },
            value: { from: "interaction.value" },
          },
        },
        {
          id: "showcase-run",
          type: "submit",
          source: "showcase_lab",
          emits: "showcase/run",
        },
        {
          id: "showcase-mode-detailed",
          type: "click",
          source: "showcase-mode-detailed",
          emits: "showcase/mode-detailed",
        },
        {
          id: "showcase-mode-concise",
          type: "click",
          source: "showcase-mode-concise",
          emits: "showcase/mode-concise",
        },
        {
          id: "showcase-open-selected",
          type: "click",
          source: "showcase-open-selected",
          emits: "showcase/open-selected",
        },
        {
          id: "showcase-open-workspace",
          type: "click",
          source: "showcase-open-workspace",
          emits: "showcase/open-workspace",
        },
        {
          id: "showcase-upgrade",
          type: "click",
          source: "showcase-upgrade",
          emits: "showcase/open-upgrade",
        },
        {
          id: "showcase-open-hub",
          type: "click",
          source: "showcase-open-hub",
          emits: "showcase/open-hub",
        },
        {
          id: "showcase-open-studio",
          type: "click",
          source: "showcase-open-studio",
          emits: "showcase/open-studio",
        },
        {
          id: "showcase-open-marketplace",
          type: "click",
          source: "showcase-open-marketplace",
          emits: "showcase/open-marketplace",
        },
      ],
    },
    logic: {
      entryEvents: ["app/init"],
      steps: [
        {
          id: "showcase-init",
          on: "app/init",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.findBySlug",
              input: {
                items: { from: "state.global.featured_scenarios" },
                slug: { from: "state.local.selected_slug" },
              },
              assign: "global.active_scenario",
            },
            {
              kind: "invoke",
              actionId: "scenarios.fetchDemoRunStatus",
              input: {
                prompt_slug: { from: "state.local.selected_slug" },
              },
              assign: "global.demo_status",
            },
            { kind: "emit", event: "showcase/rebuild-output" },
          ],
        },
        {
          id: "showcase-form-update",
          on: "form/update",
          actions: [{ kind: "set_path", targetFrom: "bind", valueFrom: "value" }],
        },
        {
          id: "showcase-selection-update",
          on: "showcase/selection-updated",
          actions: [
            { kind: "set_path", targetFrom: "bind", valueFrom: "value" },
            {
              kind: "invoke",
              actionId: "scenarios.findBySlug",
              input: {
                items: { from: "state.global.featured_scenarios" },
                slug: { from: "state.local.selected_slug" },
              },
              assign: "global.active_scenario",
            },
            {
              kind: "invoke",
              actionId: "scenarios.fetchDemoRunStatus",
              input: {
                prompt_slug: { from: "state.local.selected_slug" },
              },
              assign: "global.demo_status",
            },
            { kind: "emit", event: "showcase/rebuild-output" },
          ],
        },
        {
          id: "showcase-mode-detailed",
          on: "showcase/mode-detailed",
          actions: [
            { kind: "set", target: "local.output_mode", value: "detailed" },
            { kind: "emit", event: "showcase/rebuild-output" },
          ],
        },
        {
          id: "showcase-mode-concise",
          on: "showcase/mode-concise",
          actions: [
            { kind: "set", target: "local.output_mode", value: "concise" },
            { kind: "emit", event: "showcase/rebuild-output" },
          ],
        },
        {
          id: "showcase-build-output",
          on: "showcase/rebuild-output",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.buildLiveResult",
              input: {
                language: { from: "state.global.language" },
                title: { from: "state.global.active_scenario.title", fallback: "Scenario" },
                summary: { from: "state.global.active_scenario.summary", fallback: "No summary" },
                category: { from: "state.global.active_scenario.category", fallback: "utility" },
                task_input: { from: "state.local.scenario_input" },
                output_depth: { from: "state.local.output_mode" },
                variation_seed: { from: "state.local.variation_seed" },
              },
              assign: "global.live_result",
            },
            {
              kind: "invoke",
              actionId: "runtime.splitLines",
              input: {
                value: { from: "state.global.live_result" },
              },
              assign: "streams.live_output",
            },
          ],
        },
        {
          id: "showcase-run",
          on: "showcase/run",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.trackDemoRun",
              input: {
                prompt_slug: { from: "state.local.selected_slug" },
                task_input: { from: "state.local.scenario_input" },
              },
              assign: "local.last_run",
            },
            {
              kind: "set",
              target: "global.demo_status",
              value: { from: "state.local.last_run.status", fallback: {} },
            },
            {
              kind: "set",
              target: "ui.guard_message",
              value: { from: "state.local.last_run.message", fallback: null },
            },
            {
              kind: "append",
              target: "streams.activity",
              value: { template: "{{event.at}} · showcase run {{state.local.selected_slug}}" },
            },
            { kind: "emit", event: "showcase/rebuild-output" },
          ],
        },
        {
          id: "showcase-open-selected",
          on: "showcase/open-selected",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: { template: "/prompt/{{state.local.selected_slug}}" },
                target: "_self",
              },
            },
          ],
        },
        {
          id: "showcase-open-workspace",
          on: "showcase/open-workspace",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: { from: "state.global.links.workspace" },
                target: "_self",
              },
            },
          ],
        },
        {
          id: "showcase-open-upgrade",
          on: "showcase/open-upgrade",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "/pricing?tier=starter",
                target: "_self",
              },
            },
          ],
        },
        {
          id: "showcase-open-hub",
          on: "showcase/open-hub",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "/scenarios",
                target: "_self",
              },
            },
          ],
        },
        {
          id: "showcase-open-studio",
          on: "showcase/open-studio",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "/studio",
                target: "_self",
              },
            },
          ],
        },
        {
          id: "showcase-open-marketplace",
          on: "showcase/open-marketplace",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "/scenarios/marketplace",
                target: "_self",
              },
            },
          ],
        },
      ],
    },
    output: {
      renderer: "hybrid",
      liveUpdates: true,
      streamPath: "streams.live_output",
    },
    state: {
      variables: [
        { scope: "global", key: "language", initial: input.language },
        { scope: "global", key: "featured_scenarios", initial: featuredScenarios },
        { scope: "global", key: "active_scenario", initial: featuredScenarios[0] ?? null },
        { scope: "global", key: "live_result", initial: "" },
        { scope: "global", key: "packs", initial: input.packs.slice(0, 3) },
        { scope: "global", key: "chain_items", initial: chainItems },
        { scope: "global", key: "next_steps", initial: input.nextSteps.slice(0, 3) },
        { scope: "global", key: "return_triggers", initial: input.returnTriggers.slice(0, 3) },
        { scope: "global", key: "showcase", initial: input.showcase.slice(0, 3) },
        { scope: "global", key: "pricing_plans", initial: input.pricingPlans },
        { scope: "global", key: "demo_status", initial: {} },
        { scope: "global", key: "links.workspace", initial: input.isAuthenticated ? "/dashboard" : "/signup" },
        { scope: "global", key: "metrics.featured_count", initial: featuredScenarios.length },
        { scope: "global", key: "metrics.total_saves", initial: totalSaveSignals },
        { scope: "global", key: "metrics.high_quality", initial: highQualityScenarios },
        { scope: "local", key: "selected_slug", initial: initialSlug },
        { scope: "local", key: "scenario_input", initial: "" },
        { scope: "local", key: "output_mode", initial: "detailed" },
        { scope: "local", key: "variation_seed", initial: 0 },
        { scope: "ui", key: "guard_message", initial: null },
        { scope: "streams", key: "live_output", initial: [] },
        { scope: "streams", key: "activity", initial: [] },
      ],
      persistence: {
        key: "home-scenarios-showcase-runtime-v3",
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
      gates: [],
      usageLimits: [
        {
          id: "showcase_run",
          event: "showcase/run",
          max: 100,
          window: "session",
        },
      ],
    },
    composition: {
      pipeline: ["home-scenarios-showcase-runtime", "home-workbench-runtime", "ops-growth-dashboard"],
      sharedState: [{ from: "local.selected_slug", to: "global.shared.selected_scenario_slug" }],
    },
    sandbox: {
      allowedActions: [
        "scenarios.findBySlug",
        "scenarios.fetchDemoRunStatus",
        "scenarios.trackDemoRun",
        "scenarios.buildLiveResult",
        "runtime.splitLines",
        "runtime.navigate",
      ],
      maxActionMs: 6000,
      maxEventsPerMinute: 300,
    },
  };
}
