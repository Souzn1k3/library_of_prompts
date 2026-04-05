import type { PromptDiscoveryFilters } from "@/lib/types";

export const TECHNIQUES = ["zero_shot", "few_shot", "chain_of_thought", "other"] as const;

export const DEFAULT_DISCOVERY_FILTERS: PromptDiscoveryFilters = {
  use_cases: [],
  model_compatibility: [],
  tags: [],
  difficulties: [],
  output_types: [],
  sorts: [],
};

