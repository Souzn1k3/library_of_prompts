"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState, useTransition } from "react";

import { startRouteTransitionLoader } from "@/components/navigation/RouteTransitionLoader";
import { trackEvent } from "@/lib/analytics";
import { APP_ROUTES } from "@/lib/constants/routes";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getSortTranslationKey,
  type TranslationKey,
} from "@/lib/i18n";

import type { CatalogInitialFilters } from "@/components/catalog/types";
import type { PromptDiscoveryFilters } from "@/lib/types";

type TranslateFn = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type UseCatalogFiltersStateArgs = {
  initial: CatalogInitialFilters;
  discoveryFilters: PromptDiscoveryFilters;
  t: TranslateFn;
};

function sanitizeMultiSelected(values: string[]): string[] {
  return values.filter(Boolean);
}

function buildSearchParams(filters: CatalogInitialFilters): URLSearchParams {
  const searchParams = new URLSearchParams();
  if (filters.q) searchParams.set("q", filters.q);
  if (filters.category_id) searchParams.set("category_id", filters.category_id);
  if (filters.technique) searchParams.set("technique", filters.technique);
  if (filters.difficulty) searchParams.set("difficulty", filters.difficulty);
  if (filters.output_type) searchParams.set("output_type", filters.output_type);
  if (filters.sort) searchParams.set("sort", filters.sort);
  for (const value of filters.use_case ?? []) searchParams.append("use_case", value);
  for (const value of filters.model ?? []) searchParams.append("model", value);
  for (const value of filters.tag ?? []) searchParams.append("tag", value);
  return searchParams;
}

export function useCatalogFiltersState({ initial, discoveryFilters, t }: UseCatalogFiltersStateArgs) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [filters, setFilters] = useState<CatalogInitialFilters>(initial);

  useEffect(() => {
    setFilters(initial);
  }, [initial]);

  const sortOptions = useMemo(() => {
    const source = discoveryFilters.sorts.length
      ? discoveryFilters.sorts
      : ["relevance", "trending", "most_used", "most_saved", "newest"];
    return source.map((value) => ({
      value,
      label: t(getSortTranslationKey(value)),
    }));
  }, [discoveryFilters.sorts, t]);

  const difficultyOptions = useMemo(() => {
    const source = discoveryFilters.difficulties.length
      ? discoveryFilters.difficulties
      : ["beginner", "intermediate", "advanced"];
    return source.map((value) => ({ value, label: t(getDifficultyTranslationKey(value)) }));
  }, [discoveryFilters.difficulties, t]);

  const outputOptions = useMemo(() => {
    const source = discoveryFilters.output_types.length
      ? discoveryFilters.output_types
      : ["text", "code", "structured"];
    return source.map((value) => ({ value, label: t(getOutputTypeTranslationKey(value)) }));
  }, [discoveryFilters.output_types, t]);

  function pushFilters(next: CatalogInitialFilters) {
    setFilters(next);
    trackEvent({
      eventName: "catalog_filter_used",
      page: APP_ROUTES.catalog,
      feature: "catalog_filters",
      metadata: {
        category_id: next.category_id ?? null,
        technique: next.technique ?? null,
        difficulty: next.difficulty ?? null,
        output_type: next.output_type ?? null,
        sort: next.sort ?? null,
        use_case_count: next.use_case?.length ?? 0,
        model_count: next.model?.length ?? 0,
        tag_count: next.tag?.length ?? 0,
      },
    });
    const query = buildSearchParams(next).toString();
    startTransition(() => {
      startRouteTransitionLoader();
      router.replace(`${APP_ROUTES.catalog}${query ? `?${query}` : ""}`);
    });
  }

  function submitSearch() {
    trackEvent({
      eventName: "catalog_search_used",
      page: APP_ROUTES.catalog,
      feature: "catalog_search",
      metadata: {
        query: filters.q ?? "",
      },
    });
    pushFilters({ ...filters, q: filters.q || undefined });
  }

  return {
    filters,
    isPending,
    sortOptions,
    difficultyOptions,
    outputOptions,
    shouldFocusSearch: !(initial.q && initial.q.trim().length > 0),
    setSearchQuery: (query: string) => setFilters((prev) => ({ ...prev, q: query })),
    pushFilters,
    submitSearch,
    sanitizeMultiSelected,
  };
}
