import type { Metadata } from "next";
import Link from "next/link";

import { ApiRequestError, fetchLessons } from "@/lib/api";

export const metadata: Metadata = {
  title: "Learn",
  description: "Prompt engineering lessons (tier-gated via API).",
};

export const revalidate = 120;

export default async function LearnIndexPage() {
  let lessons: Awaited<ReturnType<typeof fetchLessons>> = [];
  let error: string | null = null;
  try {
    lessons = await fetchLessons();
  } catch (e) {
    error = e instanceof ApiRequestError ? e.message : "Could not load lessons.";
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Learn</h1>
        <p className="max-w-2xl text-sm text-zinc-600">
          Lessons are returned by the API with tier metadata. Locked lessons still appear in the list;
          open a lesson to see previews until your tier unlocks full content.
        </p>
      </header>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {lessons.length === 0 && !error ? (
        <p className="text-sm text-zinc-500">
          No lessons in the database yet. Insert rows into the <code className="font-mono text-xs">lessons</code>{" "}
          table after running migrations.
        </p>
      ) : (
        <ul className="space-y-3">
          {lessons.map((l) => (
            <li key={l.id}>
              <Link
                href={`/learn/${encodeURIComponent(l.slug)}`}
                className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm shadow-card transition hover:border-zinc-300"
              >
                <span className="font-medium text-zinc-900">{l.title}</span>
                <span className="text-xs text-zinc-500">
                  {l.locked ? "Locked" : "Open"} · {l.min_tier}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
