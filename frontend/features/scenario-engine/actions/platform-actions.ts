import {
  fetchGrowthDashboard,
  fetchRevenueDashboard,
  fetchGtmDashboard,
  upsertGtmChannelSpend,
  fetchScenarioDemoRunStatus,
  purchaseScenarioDemoRunBoost,
  trackScenarioDemoRun,
} from "@/lib/client-api";
import { buildScenarioLiveResult } from "@/features/scenarios/application/scenarioRuntime";
import { buildScenarioExplorerSnapshot } from "@/features/scenarios/application/scenarioExplorer";
import type { ScenarioDefinition as LegacyScenarioDefinition } from "@/features/scenarios/domain/scenario";

import type { ScenarioActionRegistry } from "../types";

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return fallback;
}

function asNullableString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized.length ? normalized : null;
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value);
}

function asOutputDepth(value: unknown): "concise" | "detailed" {
  return value === "concise" ? "concise" : "detailed";
}

function asScenarioCategory(
  value: unknown,
): "utility" | "learning" | "productivity" | "entertainment" | "growth" {
  if (
    value === "utility" ||
    value === "learning" ||
    value === "productivity" ||
    value === "entertainment" ||
    value === "growth"
  ) {
    return value;
  }
  return "utility";
}

function toLegacyScenarioList(value: unknown): LegacyScenarioDefinition[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is LegacyScenarioDefinition => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const row = item as Record<string, unknown>;
    return typeof row.id === "string" && typeof row.slug === "string" && typeof row.title === "string";
  });
}

function toRecordList(value: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null);
}

export const scenarioPlatformActions: ScenarioActionRegistry = {
  "analytics.fetchGrowthDashboard": async (input) => {
    const windowDays = toNumber(input.window_days, 28);
    return fetchGrowthDashboard({ windowDays });
  },
  "analytics.fetchRevenueDashboard": async (input) => {
    const windowDays = toNumber(input.window_days, 30);
    return fetchRevenueDashboard({ windowDays });
  },
  "analytics.fetchGtmDashboard": async (input) => {
    const windowDays = toNumber(input.window_days, 30);
    return fetchGtmDashboard({ windowDays });
  },
  "analytics.flattenGrowthExperimentRows": (input) => {
    const dashboard = input.dashboard as
      | {
          experiments?: Array<{
            key: string;
            variants: Array<{
              variant: string;
              users: number;
              conversion: number;
              retention_d7: number;
            }>;
          }>;
        }
      | undefined;

    const rows = (dashboard?.experiments ?? []).flatMap((experiment) =>
      experiment.variants.map((variant) => ({
        experiment: experiment.key,
        variant: variant.variant,
        users: variant.users,
        conversion: variant.conversion,
        retention_d7: variant.retention_d7,
      })),
    );
    return rows;
  },
  "analytics.upsertGtmSpend": async (input) => {
    const payload = await upsertGtmChannelSpend({
      spend_day: String(input.spend_day ?? ""),
      source: String(input.source ?? ""),
      medium: asNullableString(input.medium),
      campaign: asNullableString(input.campaign),
      ad_id: asNullableString(input.ad_id),
      creative_id: asNullableString(input.creative_id),
      cost_usd: toNumber(input.cost_usd, 0),
      clicks: toNumber(input.clicks, 0),
      impressions: toNumber(input.impressions, 0),
      dedupe_key: asNullableString(input.dedupe_key),
    });

    return {
      message: `Spend saved: ${payload.source} ${payload.campaign ?? "—"} · $${payload.cost_usd.toFixed(2)} (${payload.spend_day})`,
      entry: payload,
    };
  },
  "runtime.nowDate": () => new Date().toISOString().slice(0, 10),
  "runtime.splitLines": (input) => {
    const value = asString(input.value);
    if (!value.trim()) {
      return [];
    }
    return value.split(/\r?\n/g);
  },
  "runtime.navigate": (input) => {
    const href = asString(input.href);
    const target = asString(input.target, "_self");
    if (typeof window === "undefined" || !href) {
      return { ok: false };
    }
    if (target === "_blank") {
      window.open(href, "_blank", "noopener,noreferrer");
    } else {
      window.location.assign(href);
    }
    return { ok: true };
  },
  "scenarios.fetchDemoRunStatus": async (input) => {
    const promptSlug = asString(input.prompt_slug);
    if (!promptSlug) {
      return null;
    }
    return fetchScenarioDemoRunStatus(promptSlug);
  },
  "scenarios.trackDemoRun": async (input) => {
    const promptSlug = asString(input.prompt_slug);
    if (!promptSlug) {
      return {
        executed: false,
        status: null,
        message: "run_unavailable",
      };
    }

    try {
      const result = await trackScenarioDemoRun({
        prompt_slug: promptSlug,
        task_input: asNullableString(input.task_input),
      });
      return {
        ...result,
        message: result.executed
          ? result.status.cap_reached
            ? "free_demo_cap_reached"
            : null
          : result.status.reason ?? "run_limit_reached",
      };
    } catch {
      return {
        executed: false,
        status: null,
        message: "run_unavailable",
      };
    }
  },
  "scenarios.purchaseDemoRunBoost": async (input) => {
    const promptSlug = asString(input.prompt_slug);
    if (!promptSlug) {
      return {
        message: "boost_purchase_failed",
      };
    }
    try {
      const purchase = await purchaseScenarioDemoRunBoost({ prompt_slug: promptSlug });
      return {
        ...purchase,
        message: purchase.is_pro ? "pro_unlimited_runs" : `bonus_runs_added:${purchase.applied_bonus_runs}`,
      };
    } catch {
      return {
        message: "boost_purchase_failed",
      };
    }
  },
  "scenarios.buildLiveResult": (input) => {
    const language = asString(input.language, "en") as "en" | "ru" | "tt";
    const category = asScenarioCategory(input.category);
    const scenario = {
      title: asString(input.title, "Scenario"),
      summary: asString(input.summary, "Scenario output"),
      category,
    };

    return buildScenarioLiveResult({
      language,
      scenario,
      taskInput: asString(input.task_input),
      outputDepth: asOutputDepth(input.output_depth),
      variationSeed: toNumber(input.variation_seed, 0),
    });
  },
  "scenarios.computeSelection": (input) => {
    const scenarios = toLegacyScenarioList(input.scenarios);
    const state = buildScenarioExplorerSnapshot(scenarios, {
      query: asString(input.query),
      selectedTechnique: "all",
      selectedFacet: null,
      selectedSlug: asNullableString(input.selected_slug),
    });
    return {
      filtered: state.filteredScenarios,
      visible: state.visibleScenarios,
      selected: state.selectedScenario,
      has_active_filters: state.hasActiveFilters,
    };
  },
  "scenarios.findBySlug": (input) => {
    const items = toRecordList(input.items);
    const slug = asString(input.slug);
    if (!items.length) {
      return null;
    }
    return items.find((item) => asString(item.slug) === slug) ?? items[0] ?? null;
  },
  "runtime.noop": () => null,
};
