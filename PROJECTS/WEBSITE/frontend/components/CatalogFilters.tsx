"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import type { Category } from "@/lib/types";

export function CatalogFilters({
  categories,
  initial,
}: {
  categories: Category[];
  initial: { q?: string; category_id?: string; technique?: string };
}) {
  const { t } = useI18n();
  const techniques = [
    { value: "", label: t("catalogFilters.allTechniques") },
    { value: "zero_shot", label: t("catalogFilters.zeroShot") },
    { value: "few_shot", label: t("catalogFilters.fewShot") },
    { value: "chain_of_thought", label: t("catalogFilters.chainOfThought") },
    { value: "other", label: t("catalogFilters.other") },
  ] as const;

  return (
    <form
      action="/catalog"
      method="get"
      className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-zinc-50/60 p-4 sm:flex-row sm:flex-wrap sm:items-end"
    >
      <div className="min-w-[220px] flex-1 space-y-1">
        <label htmlFor="q" className="text-xs font-medium text-zinc-700">
          {t("catalogFilters.search")}
        </label>
        <input
          id="q"
          name="q"
          defaultValue={initial.q ?? ""}
          placeholder={t("catalogFilters.searchPlaceholder")}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        />
      </div>
      <div className="min-w-[180px] space-y-1">
        <label htmlFor="category_id" className="text-xs font-medium text-zinc-700">
          {t("catalogFilters.category")}
        </label>
        <select
          id="category_id"
          name="category_id"
          defaultValue={initial.category_id ?? ""}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        >
          <option value="">{t("catalogFilters.allCategories")}</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="min-w-[180px] space-y-1">
        <label htmlFor="technique" className="text-xs font-medium text-zinc-700">
          {t("catalogFilters.technique")}
        </label>
        <select
          id="technique"
          name="technique"
          defaultValue={initial.technique ?? ""}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        >
          {techniques.map((tech) => (
            <option key={tech.value || "all"} value={tech.value}>
              {tech.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800"
        >
          {t("catalogFilters.apply")}
        </button>
        <a
          href="/catalog"
          className="inline-flex items-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 transition hover:border-zinc-400"
        >
          {t("catalogFilters.reset")}
        </a>
      </div>
    </form>
  );
}
