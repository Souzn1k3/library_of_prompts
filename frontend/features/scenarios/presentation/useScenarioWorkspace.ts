"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { fetchScenarioWorkspace, trackScenarioWorkspaceAction } from "@/lib/client-api";
import type { ScenarioWorkspaceAction, ScenarioWorkspaceRead } from "@/lib/types";
import { useCallback, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "pv_scenario_workspace_v1";
const MAX_RECENT = 8;
const MAX_UNFINISHED = 6;

type WorkspaceSnapshot = {
  recentSlugs: string[];
  savedSlugs: string[];
  unfinished: Array<{ slug: string; task: string; updatedAt: string }>;
};

const EMPTY_SNAPSHOT: WorkspaceSnapshot = {
  recentSlugs: [],
  savedSlugs: [],
  unfinished: [],
};

function readSnapshot(): WorkspaceSnapshot {
  if (typeof window === "undefined") {
    return EMPTY_SNAPSHOT;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return EMPTY_SNAPSHOT;
    }
    const parsed = JSON.parse(raw) as Partial<WorkspaceSnapshot>;
    return {
      recentSlugs: Array.isArray(parsed.recentSlugs)
        ? parsed.recentSlugs.filter((item): item is string => typeof item === "string")
        : [],
      savedSlugs: Array.isArray(parsed.savedSlugs)
        ? parsed.savedSlugs.filter((item): item is string => typeof item === "string")
        : [],
      unfinished: Array.isArray(parsed.unfinished)
        ? parsed.unfinished
            .filter(
              (item): item is { slug: string; task: string; updatedAt: string } =>
                typeof item?.slug === "string" &&
                typeof item?.task === "string" &&
                typeof item?.updatedAt === "string",
            )
            .slice(0, MAX_UNFINISHED)
        : [],
    };
  } catch {
    return EMPTY_SNAPSHOT;
  }
}

function writeSnapshot(snapshot: WorkspaceSnapshot) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
}

function uniqueTrimmed(values: string[], limit: number): string[] {
  const unique = Array.from(new Set(values.filter(Boolean)));
  return unique.slice(0, limit);
}

function fromServerWorkspace(workspace: ScenarioWorkspaceRead): WorkspaceSnapshot {
  return {
    recentSlugs: uniqueTrimmed(
      workspace.recent.map((item) => item.prompt.slug),
      MAX_RECENT,
    ),
    savedSlugs: uniqueTrimmed(
      workspace.saved.map((item) => item.prompt.slug),
      64,
    ),
    unfinished: workspace.unfinished
      .filter((item) => Boolean(item.unfinished_task))
      .slice(0, MAX_UNFINISHED)
      .map((item) => ({
        slug: item.prompt.slug,
        task: item.unfinished_task ?? "",
        updatedAt: item.last_used_at,
      })),
  };
}

function applyLocalAction(
  snapshot: WorkspaceSnapshot,
  *,
  action: ScenarioWorkspaceAction,
  slug: string,
  task: string | null,
): WorkspaceSnapshot {
  const cleanSlug = slug.trim();
  if (!cleanSlug) {
    return snapshot;
  }

  const now = new Date().toISOString();
  const nextRecent = uniqueTrimmed([cleanSlug, ...snapshot.recentSlugs.filter((item) => item !== cleanSlug)], MAX_RECENT);
  let nextSaved = [...snapshot.savedSlugs];
  let nextUnfinished = [...snapshot.unfinished];

  if (action === "save") {
    nextSaved = uniqueTrimmed([cleanSlug, ...nextSaved], 64);
  }
  if (action === "unsave") {
    nextSaved = nextSaved.filter((item) => item !== cleanSlug);
  }
  if (action === "unfinished_update") {
    const cleanTask = (task ?? "").trim();
    if (cleanTask) {
      nextUnfinished = [{ slug: cleanSlug, task: cleanTask, updatedAt: now }, ...nextUnfinished.filter((item) => item.slug !== cleanSlug)].slice(0, MAX_UNFINISHED);
    }
  }
  if (action === "unfinished_clear") {
    nextUnfinished = nextUnfinished.filter((item) => item.slug !== cleanSlug);
  }
  if (action === "open" || action === "run") {
    const cleanTask = (task ?? "").trim();
    if (cleanTask) {
      nextUnfinished = [{ slug: cleanSlug, task: cleanTask, updatedAt: now }, ...nextUnfinished.filter((item) => item.slug !== cleanSlug)].slice(0, MAX_UNFINISHED);
    }
  }

  return {
    recentSlugs: nextRecent,
    savedSlugs: nextSaved,
    unfinished: nextUnfinished,
  };
}

export function useScenarioWorkspace() {
  const { isAuthenticated, status } = useAuth();
  const [snapshot, setSnapshot] = useState<WorkspaceSnapshot>(EMPTY_SNAPSHOT);

  const persistLocal = useCallback((next: WorkspaceSnapshot) => {
    setSnapshot(next);
    writeSnapshot(next);
  }, []);

  const syncFromServer = useCallback(async () => {
    try {
      const workspace = await fetchScenarioWorkspace();
      const next = fromServerWorkspace(workspace);
      setSnapshot(next);
      writeSnapshot(next);
    } catch {
      const local = readSnapshot();
      setSnapshot(local);
    }
  }, []);

  useEffect(() => {
    if (status === "loading") {
      return;
    }
    if (isAuthenticated) {
      void syncFromServer();
      return;
    }
    setSnapshot(readSnapshot());
  }, [isAuthenticated, status, syncFromServer]);

  const applyAction = useCallback(
    (action: ScenarioWorkspaceAction, slug: string, task?: string | null) => {
      const optimistic = applyLocalAction(snapshot, {
        action,
        slug,
        task: task ?? null,
      });
      persistLocal(optimistic);

      if (!isAuthenticated) {
        return;
      }

      void trackScenarioWorkspaceAction({
        prompt_slug: slug,
        action,
        task_input: task ?? undefined,
      })
        .then((result) => {
          const next = fromServerWorkspace(result.workspace);
          setSnapshot(next);
          writeSnapshot(next);
        })
        .catch(() => {
          // Keep optimistic local state if server sync fails.
        });
    },
    [isAuthenticated, persistLocal, snapshot],
  );

  const markRecent = useCallback(
    (slug: string) => {
      applyAction("open", slug, null);
    },
    [applyAction],
  );

  const toggleSaved = useCallback(
    (slug: string) => {
      const isSaved = snapshot.savedSlugs.includes(slug);
      applyAction(isSaved ? "unsave" : "save", slug, null);
    },
    [applyAction, snapshot.savedSlugs],
  );

  const saveUnfinished = useCallback(
    (slug: string, task: string) => {
      applyAction("unfinished_update", slug, task);
    },
    [applyAction],
  );

  const clearUnfinished = useCallback(
    (slug: string) => {
      applyAction("unfinished_clear", slug, null);
    },
    [applyAction],
  );

  const trackRun = useCallback(
    (slug: string, task?: string | null) => {
      applyAction("run", slug, task ?? null);
    },
    [applyAction],
  );

  const trackCopy = useCallback(
    (slug: string) => {
      applyAction("copy", slug, null);
    },
    [applyAction],
  );

  const trackShare = useCallback(
    (slug: string) => {
      applyAction("share", slug, null);
    },
    [applyAction],
  );

  return useMemo(
    () => ({
      recentSlugs: snapshot.recentSlugs,
      savedSlugs: snapshot.savedSlugs,
      unfinished: snapshot.unfinished,
      markRecent,
      toggleSaved,
      saveUnfinished,
      clearUnfinished,
      trackRun,
      trackCopy,
      trackShare,
      refresh: syncFromServer,
    }),
    [
      clearUnfinished,
      markRecent,
      saveUnfinished,
      snapshot.recentSlugs,
      snapshot.savedSlugs,
      snapshot.unfinished,
      syncFromServer,
      toggleSaved,
      trackRun,
      trackCopy,
      trackShare,
    ],
  );
}
