"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState, useTransition } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { trackEvent } from "@/lib/analytics";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getSortTranslationKey,
} from "@/lib/i18n";
import type { Category, PromptDiscoveryFilters } from "@/lib/types";

type InitialFilters = {
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

export function CatalogFilters({
  categories,
  discoveryFilters,
  initial,
}: {
  categories: Category[];
  discoveryFilters: PromptDiscoveryFilters;
  initial: InitialFilters;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [filters, setFilters] = useState<InitialFilters>(initial);
  const { t } = useI18n();

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

  function pushFilters(next: InitialFilters) {
    setFilters(next);
    trackEvent({
      eventName: "catalog_filter_used",
      page: "/catalog",
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
    const sp = new URLSearchParams();
    if (next.q) sp.set("q", next.q);
    if (next.category_id) sp.set("category_id", next.category_id);
    if (next.technique) sp.set("technique", next.technique);
    if (next.difficulty) sp.set("difficulty", next.difficulty);
    if (next.output_type) sp.set("output_type", next.output_type);
    if (next.sort) sp.set("sort", next.sort);
    for (const value of next.use_case ?? []) sp.append("use_case", value);
    for (const value of next.model ?? []) sp.append("model", value);
    for (const value of next.tag ?? []) sp.append("tag", value);
    const q = sp.toString();
    startTransition(() => {
      router.replace(`/catalog${q ? `?${q}` : ""}`);
    });
  }

  function onSearchSubmit(e: FormEvent) {
    e.preventDefault();
    trackEvent({
      eventName: "catalog_search_used",
      page: "/catalog",
      feature: "catalog_search",
      metadata: {
        query: filters.q ?? "",
      },
    });
    pushFilters({ ...filters, q: filters.q || undefined });
  }

  function parseMultiSelected(values: string[]) {
    return values.filter(Boolean);
  }

  return (
    <div className="space-y-4 rounded-lg border border-zinc-200 bg-zinc-50/60 p-4">
      <form onSubmit={onSearchSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="min-w-[220px] flex-1 space-y-1">
          <label htmlFor="q" className="text-xs font-medium text-zinc-700">
            {t("catalogFilters.search")}
          </label>
          <input
            id="q"
            name="q"
            value={filters.q ?? ""}
            onChange={(e) => setFilters((prev) => ({ ...prev, q: e.target.value }))}
            placeholder={t("catalogFilters.searchPlaceholder")}
            className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          />
        </div>
        <button
          type="submit"
          disabled={isPending}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-60"
        >
          {isPending ? t("catalogFilters.updating") : t("catalogFilters.apply")}
        </button>
        <Link
          href="/catalog"
          className="inline-flex items-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 transition hover:border-zinc-400"
        >
          {t("catalogFilters.reset")}
        </Link>
      </form>

      <div className="grid gap-3 md:grid-cols-3">
        <SelectField
          label={t("catalogFilters.category")}
          value={filters.category_id ?? ""}
          options={[
            { value: "", label: t("catalogFilters.allCategories") },
            ...categories.map((c) => ({ value: c.id, label: c.name })),
          ]}
          onChange={(value) => pushFilters({ ...filters, category_id: value || undefined })}
        />
        <SelectField
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
        <SelectField
          label={t("catalogFilters.sort")}
          value={filters.sort ?? "relevance"}
          options={sortOptions}
          onChange={(value) => pushFilters({ ...filters, sort: value || "relevance" })}
        />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <SelectField
          label={t("catalogFilters.difficulty")}
          value={filters.difficulty ?? ""}
          options={[
            { value: "", label: t("catalogFilters.allLevels") },
            ...difficultyOptions,
          ]}
          onChange={(value) => pushFilters({ ...filters, difficulty: value || undefined })}
        />
        <SelectField
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
        <MultiSelectField
          label={t("catalogFilters.useCase")}
          options={discoveryFilters.use_cases}
          selected={filters.use_case ?? []}
          onChange={(values) => pushFilters({ ...filters, use_case: parseMultiSelected(values) })}
        />
        <MultiSelectField
          label={t("catalogFilters.model")}
          options={discoveryFilters.model_compatibility}
          selected={filters.model ?? []}
          onChange={(values) => pushFilters({ ...filters, model: parseMultiSelected(values) })}
        />
        <MultiSelectField
          label={t("catalogFilters.tags")}
          options={discoveryFilters.tags}
          selected={filters.tag ?? []}
          onChange={(values) => pushFilters({ ...filters, tag: parseMultiSelected(values) })}
        />
      </div>
    </div>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-zinc-700">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
      >
        {options.map((opt) => (
          <option key={`${label}-${opt.value || "all"}`} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function MultiSelectField({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: Array<{ slug: string; name: string }>;
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-zinc-700">{label}</label>
      <select
        multiple
        value={selected}
        onChange={(e) => {
          const values = Array.from(e.target.selectedOptions).map((item) => item.value);
          onChange(values);
        }}
        className="h-28 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
      >
        {options.map((opt) => (
          <option key={`${label}-${opt.slug}`} value={opt.slug}>
            {opt.name}
          </option>
        ))}
      </select>
    </div>
  );
}
