"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { ApiRequestError, getApiBaseUrl } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { submitPrompt } from "@/lib/client-api";
import type { Category } from "@/lib/types";

const TECHNIQUES = [
  { value: "zero_shot", label: "Zero-shot" },
  { value: "few_shot", label: "Few-shot" },
  { value: "chain_of_thought", label: "Chain-of-thought" },
  { value: "other", label: "Other" },
] as const;

export function SubmitPromptForm() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/v1/categories`);
        if (!res.ok) throw new Error("bad response");
        setCategories((await res.json()) as Category[]);
      } catch {
        setCategories([]);
      }
    }
    load();
  }, []);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    if (!getToken()) {
      setError("You must be logged in to submit.");
      return;
    }
    setPending(true);
    const fd = new FormData(e.currentTarget);
    try {
      await submitPrompt({
        slug: String(fd.get("slug") ?? ""),
        title: String(fd.get("title") ?? ""),
        body: String(fd.get("body") ?? ""),
        summary: String(fd.get("summary") ?? "") || null,
        category_id: String(fd.get("category_id") ?? ""),
        technique: String(fd.get("technique") ?? "other"),
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Submit failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="slug">
          Slug (kebab-case)
        </label>
        <input
          id="slug"
          name="slug"
          required
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          placeholder="my-prompt-name"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="title">
          Title
        </label>
        <input
          id="title"
          name="title"
          required
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="category_id">
          Category
        </label>
        <select
          id="category_id"
          name="category_id"
          required
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          defaultValue=""
        >
          <option value="" disabled>
            Select…
          </option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="technique">
          Technique
        </label>
        <select
          id="technique"
          name="technique"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
          defaultValue="other"
        >
          {TECHNIQUES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="summary">
          Summary (optional)
        </label>
        <input
          id="summary"
          name="summary"
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none ring-zinc-900 focus:ring-2"
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-medium text-zinc-700" htmlFor="body">
          Prompt body
        </label>
        <textarea
          id="body"
          name="body"
          required
          rows={10}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 font-mono text-sm outline-none ring-zinc-900 focus:ring-2"
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-60"
      >
        {pending ? "Submitting…" : "Submit for review"}
      </button>
    </form>
  );
}
