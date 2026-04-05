"use client";

import Link from "next/link";
import type { FormEvent } from "react";

import {
  CatalogMultiSelectField,
  CatalogSelectField,
} from "@/components/catalog/CatalogFilterFields";
import type { CatalogFiltersProps } from "@/components/catalog/types";
import { useCatalogFiltersState } from "@/components/catalog/useCatalogFiltersState";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { APP_ROUTES } from "@/lib/constants/routes";

export function CatalogFilters({ categories, discoveryFilters, initial }: CatalogFiltersProps) {
  const { t } = useI18n();
  const {
    filters,
    isPending,
    sortOptions,
    difficultyOptions,
    outputOptions,
    shouldFocusSearch,
    setSearchQuery,
    pushFilters,
    submitSearch,
    sanitizeMultiSelected,
  } = useCatalogFiltersState({ initial, discoveryFilters, t });

  function onSearchSubmit(event: FormEvent) {
    event.preventDefault();
    submitSearch();
  }

  return (
    <div className="pv-panel space-y-5 px-5 py-5 sm:px-6">
      <form onSubmit={onSearchSubmit} className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_auto_auto] xl:items-end">
        <div className="min-w-[220px] space-y-1">
          <label htmlFor="q" className="pv-label">
            {t("catalogFilters.search")}
          </label>
          <input
            id="q"
            name="q"
            value={filters.q ?? ""}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder={t("catalogFilters.searchPlaceholder")}
            autoFocus={shouldFocusSearch}
            className="pv-input"
          />
        </div>
        <button
          type="submit"
          disabled={isPending}
          className="pv-button-primary disabled:opacity-60"
        >
          {isPending ? t("catalogFilters.updating") : t("catalogFilters.apply")}
        </button>
        <Link href={APP_ROUTES.catalog} className="pv-button-secondary">
          {t("catalogFilters.reset")}
        </Link>
      </form>

      <div className="grid gap-3 md:grid-cols-3">
        <CatalogSelectField
          label={t("catalogFilters.category")}
          value={filters.category_id ?? ""}
          options={[
            { value: "", label: t("catalogFilters.allCategories") },
            ...categories.map((category) => ({ value: category.id, label: category.name })),
          ]}
          onChange={(value) => pushFilters({ ...filters, category_id: value || undefined })}
        />
        <CatalogSelectField
          label={t("catalogFilters.technique")}
          value={filters.technique ?? ""}
          options={[
            { value: "", label: t("catalogFilters.allTechniques") },
            { value: "zero_shot", label: t("catalogFilters.zeroShot") },
            { value: "few_shot", label: t("catalogFilters.fewShot") },
            { value: "chain_of_thought", label: t("catalogFilters.chainOfThought") },
            { value: "other", label: t("catalogFilters.other") },
          ]}
          onChange={(value) => pushFilters({ ...filters, technique: value || undefined })}
        />
        <CatalogSelectField
          label={t("catalogFilters.sort")}
          value={filters.sort ?? "relevance"}
          options={sortOptions}
          onChange={(value) => pushFilters({ ...filters, sort: value || "relevance" })}
        />
      </div>

      <details className="pv-details">
        <summary>{t("catalogFilters.advanced")}</summary>
        <p className="mt-2 pv-hint-badge">{t("common.hintBadge")}</p>
        <p className="mt-1 text-sm text-zinc-600">{t("catalogFilters.advancedHint")}</p>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <CatalogSelectField
            label={t("catalogFilters.difficulty")}
            value={filters.difficulty ?? ""}
            options={[
              { value: "", label: t("catalogFilters.allLevels") },
              ...difficultyOptions,
            ]}
            onChange={(value) => pushFilters({ ...filters, difficulty: value || undefined })}
          />
          <CatalogSelectField
            label={t("catalogFilters.output")}
            value={filters.output_type ?? ""}
            options={[
              { value: "", label: t("catalogFilters.allOutputs") },
              ...outputOptions,
            ]}
            onChange={(value) => pushFilters({ ...filters, output_type: value || undefined })}
          />
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <CatalogMultiSelectField
            label={t("catalogFilters.useCase")}
            options={discoveryFilters.use_cases}
            selected={filters.use_case ?? []}
            onChange={(values) => pushFilters({ ...filters, use_case: sanitizeMultiSelected(values) })}
          />
          <CatalogMultiSelectField
            label={t("catalogFilters.model")}
            options={discoveryFilters.model_compatibility}
            selected={filters.model ?? []}
            onChange={(values) => pushFilters({ ...filters, model: sanitizeMultiSelected(values) })}
          />
          <CatalogMultiSelectField
            label={t("catalogFilters.tags")}
            options={discoveryFilters.tags}
            selected={filters.tag ?? []}
            onChange={(values) => pushFilters({ ...filters, tag: sanitizeMultiSelected(values) })}
          />
        </div>
      </details>
    </div>
  );
}
