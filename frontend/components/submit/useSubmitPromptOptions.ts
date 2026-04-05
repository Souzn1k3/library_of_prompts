"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchCategories, fetchPromptDiscoveryFilters } from "@/lib/api";
import type { TranslationKey } from "@/lib/i18n";
import type { Category, PromptDiscoveryFilters } from "@/lib/types";

import { DEFAULT_DISCOVERY_FILTERS } from "@/components/submit/constants";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type UseSubmitPromptOptionsArgs = {
  language: string;
  t: Translate;
};

export function useSubmitPromptOptions({ language, t }: UseSubmitPromptOptionsArgs) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [discoveryFilters, setDiscoveryFilters] = useState<PromptDiscoveryFilters>(
    DEFAULT_DISCOVERY_FILTERS,
  );
  const [bootstrapLoading, setBootstrapLoading] = useState(true);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reloadOptions = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadOptions() {
      setBootstrapLoading(true);
      setBootstrapError(null);
      try {
        const [categoryRows, filterRows] = await Promise.all([
          fetchCategories(null, language),
          fetchPromptDiscoveryFilters(null, language),
        ]);
        if (cancelled) {
          return;
        }
        setCategories(categoryRows);
        setDiscoveryFilters(filterRows);
      } catch {
        if (cancelled) {
          return;
        }
        setCategories([]);
        setDiscoveryFilters(DEFAULT_DISCOVERY_FILTERS);
        setBootstrapError(t("submit.optionsLoadFailed"));
      } finally {
        if (!cancelled) {
          setBootstrapLoading(false);
        }
      }
    }

    void loadOptions();

    return () => {
      cancelled = true;
    };
  }, [language, reloadToken, t]);

  return {
    categories,
    discoveryFilters,
    bootstrapLoading,
    bootstrapError,
    reloadOptions,
  };
}
