"use client";

import { useEffect, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { fetchSavedPrompts, savePrompt, unsavePrompt } from "@/lib/client-api";

export function SavePromptButton({ promptId }: { promptId: string }) {
  const [authed, setAuthed] = useState(false);
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  useEffect(() => {
    if (!getToken()) return;
    fetchSavedPrompts()
      .then((list) => setSaved(list.some((p) => p.id === promptId)))
      .catch(() => {});
  }, [promptId]);

  async function toggle() {
    setError(null);
    setPending(true);
    try {
      if (saved) {
        await unsavePrompt(promptId);
        setSaved(false);
      } else {
        await savePrompt(promptId);
        setSaved(true);
      }
    } catch (e) {
      if (e instanceof ApiRequestError && e.status === 409) {
        setSaved(true);
      } else {
        setError(e instanceof ApiRequestError ? e.message : "Could not update");
      }
    } finally {
      setPending(false);
    }
  }

  if (!authed) {
    return (
      <p className="text-sm text-zinc-500">
        <a href="/login" className="font-medium text-zinc-900 underline">
          Log in
        </a>{" "}
        to save prompts to your dashboard.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={toggle}
        disabled={pending}
        className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-900 transition hover:border-zinc-400 disabled:opacity-60"
      >
        {pending ? "Updating…" : saved ? "Saved — remove" : "Save to dashboard"}
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}
