"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PromptCard } from "@/components/PromptCard";
import { ApiRequestError } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { fetchSavedPrompts } from "@/lib/client-api";
import type { PromptListItem } from "@/lib/types";

export function DashboardClient() {
  const [items, setItems] = useState<PromptListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      setError("signed_out");
      setItems([]);
      return;
    }
    fetchSavedPrompts()
      .then((list) => {
        setItems(list);
        setError(null);
      })
      .catch((e) => {
        setError(e instanceof ApiRequestError ? e.message : "Failed to load saved prompts");
        setItems([]);
      });
  }, []);

  if (error === "signed_out") {
    return (
      <p className="text-sm text-zinc-600">
        Please{" "}
        <Link href="/login" className="font-medium text-zinc-900 underline">
          log in
        </Link>{" "}
        to view saved prompts.
      </p>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        {error}
      </div>
    );
  }

  if (items === null) {
    return <p className="text-sm text-zinc-500">Loading…</p>;
  }

  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-8 text-center text-sm text-zinc-600">
        No saved prompts yet. Browse the{" "}
        <Link href="/catalog" className="font-medium text-zinc-900 underline">
          catalog
        </Link>{" "}
        and save prompts you want to reuse.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {items.map((p) => (
        <PromptCard key={p.id} prompt={p} />
      ))}
    </div>
  );
}
