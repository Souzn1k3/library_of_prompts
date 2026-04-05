"use client";

import type { Category, PromptDiscoveryFilters } from "@/lib/types";

export type CatalogInitialFilters = {
  q?: string;
  category_id?: string;
  technique?: string;
  difficulty?: string;
  output_type?: string;
  sort?: string;
  use_case?: string[];
  model?: string[];
  tag?: string[];
};

export type CatalogFiltersProps = {
  categories: Category[];
  discoveryFilters: PromptDiscoveryFilters;
  initial: CatalogInitialFilters;
};
