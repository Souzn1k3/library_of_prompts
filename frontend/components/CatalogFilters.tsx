"use client";

import Link from "next/link";
import { useMemo, type FormEvent } from "react";

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
  const activeFiltersCount = useMemo(() => {
    return [
      filters.category_id ? 1 : 0,
      filters.technique ? 1 : 0,
      filters.difficulty ? 1 : 0,
      filters.output_type ? 1 : 0,
      filters.use_case?.length ?? 0,
      filters.model?.length ?? 0,
      filters.tag?.length ?? 0,
    ].reduce((sum, value) => sum + value, 0);
  }, [filters]);

  function onSearchSubmit(event: FormEvent) {
    event.preventDefault();
    submitSearch();
  }

  return (
    <div className="pv-panel px-5 py-4 sm:px-6">
      <form onSubmit={onSearchSubmit} className="flex flex-wrap items-center gap-2 sm:gap-3">
        <label htmlFor="q" className="sr-only">
          {t("catalogFilters.search")}
        </label>
        <div className="min-w-[220px] flex-1">
          <input
            id="q"
            name="q"
            value={filters.q ?? ""}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder={t("catalogFilters.searchPlaceholder")}
            autoFocus={shouldFocusSearch}
            className="pv-input h-10"
          />
        </div>
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[var(--pv-border)] text-zinc-600 transition hover:border-[var(--pv-border-strong)] hover:text-[var(--pv-brand-strong)] disabled:opacity-60"
          aria-label={isPending ? t("catalogFilters.updating") : t("catalogFilters.apply")}
          title={isPending ? t("catalogFilters.updating") : t("catalogFilters.apply")}
        >
          <svg
            aria-hidden="true"
            viewBox="0 0 20 20"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="9" cy="9" r="5.5" />
            <path d="m13 13 4 4" />
          </svg>
        </button>

        <details className="relative">
          <summary
            className="inline-flex h-10 w-10 cursor-pointer list-none items-center justify-center rounded-full text-zinc-500 transition hover:text-[var(--pv-brand-strong)] [&::-webkit-details-marker]:hidden"
            aria-label={t("catalogFilters.sort")}
            title={t("catalogFilters.sort")}
          >
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m6 6 4-4 4 4" />
              <path d="M10 2v20" />
              <path d="m18 18-4 4-4-4" />
              <path d="M14 2v20" />
            </svg>
          </summary>
          <div className="absolute right-0 top-[calc(100%+0.5rem)] z-20 w-60">
            <div className="pv-floating-menu gap-1.5 p-2">
              {sortOptions.map((option) => {
                const isActive = (filters.sort ?? "relevance") === option.value;
                return (
                  <button
                    key={`sort-${option.value}`}
                    type="button"
                    onClick={() => pushFilters({ ...filters, sort: option.value || "relevance" })}
                    className={`flex w-full items-center justify-between rounded-[0.85rem] px-3 py-2 text-sm transition ${
                      isActive
                        ? "bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]"
                        : "text-zinc-700 hover:bg-[var(--pv-surface-muted)]"
                    }`}
                  >
                    <span>{option.label}</span>
                    {isActive ? <span aria-hidden="true">✓</span> : null}
                  </button>
                );
              })}
            </div>
          </div>
        </details>

        <details className="relative">
          <summary className="pv-button-secondary !min-h-0 !w-auto list-none px-3 py-2 text-sm [&::-webkit-details-marker]:hidden">
            <span>{t("catalogFilters.filters")}</span>
            {activeFiltersCount > 0 ? (
              <span className="ml-1 inline-flex min-w-5 items-center justify-center rounded-full bg-[var(--pv-brand-soft)] px-1.5 text-xs font-semibold text-[var(--pv-brand-strong)]">
                {activeFiltersCount}
              </span>
            ) : null}
          </summary>
          <div className="absolute right-0 top-[calc(100%+0.5rem)] z-20 w-[min(92vw,760px)]">
            <div className="pv-floating-menu p-3 sm:p-4">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
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

              <div className="grid gap-3 md:grid-cols-3">
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

              <div className="flex justify-end">
                <Link href={APP_ROUTES.catalog} className="text-sm font-medium text-zinc-500 transition hover:text-zinc-900">
                  {t("catalogFilters.reset")}
                </Link>
              </div>
            </div>
          </div>
        </details>

        <Link href={APP_ROUTES.catalog} className="text-sm font-medium text-zinc-500 transition hover:text-zinc-900">
          {t("catalogFilters.reset")}
        </Link>
      </form>
    </div>
  );
}
