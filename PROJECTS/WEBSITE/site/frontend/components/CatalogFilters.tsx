import type { Category } from "@/lib/types";

const TECHNIQUES = [
  { value: "", label: "All techniques" },
  { value: "zero_shot", label: "Zero-shot" },
  { value: "few_shot", label: "Few-shot" },
  { value: "chain_of_thought", label: "Chain-of-thought" },
  { value: "other", label: "Other" },
] as const;

export function CatalogFilters({
  categories,
  initial,
}: {
  categories: Category[];
  initial: { q?: string; category_id?: string; technique?: string };
}) {
  return (
    <form
      action="/catalog"
      method="get"
      className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-zinc-50/60 p-4 sm:flex-row sm:flex-wrap sm:items-end"
    >
      <div className="min-w-[220px] flex-1 space-y-1">
        <label htmlFor="q" className="text-xs font-medium text-zinc-700">
          Search
        </label>
        <input
          id="q"
          name="q"
          defaultValue={initial.q ?? ""}
          placeholder="Search title or body"
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        />
      </div>
      <div className="min-w-[180px] space-y-1">
        <label htmlFor="category_id" className="text-xs font-medium text-zinc-700">
          Category
        </label>
        <select
          id="category_id"
          name="category_id"
          defaultValue={initial.category_id ?? ""}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="min-w-[180px] space-y-1">
        <label htmlFor="technique" className="text-xs font-medium text-zinc-700">
          Technique
        </label>
        <select
          id="technique"
          name="technique"
          defaultValue={initial.technique ?? ""}
          className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        >
          {TECHNIQUES.map((t) => (
            <option key={t.value || "all"} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800"
        >
          Apply
        </button>
        <a
          href="/catalog"
          className="inline-flex items-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 transition hover:border-zinc-400"
        >
          Reset
        </a>
      </div>
    </form>
  );
}
