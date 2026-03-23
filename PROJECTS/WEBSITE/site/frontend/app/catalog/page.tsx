import type { Metadata } from "next";

import { CatalogFilters } from "@/components/CatalogFilters";
import { PromptCard } from "@/components/PromptCard";
import { ApiRequestError, fetchCategories, fetchPrompts } from "@/lib/api";
import type { Category, PromptListItem } from "@/lib/types";

export const metadata: Metadata = {
  title: "Catalog",
  description: "Browse categories and published prompts from the Prompts Vault API.",
};

export const revalidate = 60;

function firstParam(v: string | string[] | undefined): string | undefined {
  if (typeof v === "string") return v;
  if (Array.isArray(v) && v.length > 0) return v[0];
  return undefined;
}

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CatalogPage({ searchParams }: PageProps) {
  const sp = (await searchParams) ?? {};
  const q = firstParam(sp.q);
  const category_id = firstParam(sp.category_id);
  const technique = firstParam(sp.technique);

  let categories: Category[] = [];
  let prompts: PromptListItem[] = [];
  let error: string | null = null;

  try {
    [categories, prompts] = await Promise.all([
      fetchCategories(),
      fetchPrompts({
        limit: 50,
        q: q || undefined,
        category_id: category_id || undefined,
        technique: technique || undefined,
      }),
    ]);
  } catch (e) {
    if (e instanceof ApiRequestError) {
      error = e.message;
    } else {
      error = "Could not reach the API. Is the backend running?";
    }
  }

  return (
    <div className="space-y-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Catalog</h1>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">
          Search published prompts, filter by category and technique. Data comes from{" "}
          <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-xs text-zinc-800">
            NEXT_PUBLIC_API_URL
          </code>
          .
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-medium">Catalog unavailable</p>
          <p className="mt-1 text-amber-800">{error}</p>
        </div>
      ) : null}

      {!error ? (
        <CatalogFilters
          categories={categories}
          initial={{ q, category_id, technique }}
        />
      ) : null}

      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          Categories
        </h2>
        {categories.length === 0 ? (
          <p className="text-sm text-zinc-500">No categories yet.</p>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {categories.map((c) => (
              <li
                key={c.id}
                className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-800"
              >
                {c.name}
                {c.is_restricted ? (
                  <span className="ml-1 text-zinc-400">(restricted)</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
          Prompts
        </h2>
        {prompts.length === 0 ? (
          <p className="text-sm text-zinc-500">
            No prompts match these filters. Try resetting search or seeding published prompts in
            the API.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {prompts.map((p) => (
              <PromptCard key={p.id} prompt={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
