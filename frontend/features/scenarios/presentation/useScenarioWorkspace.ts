"use client";

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

export function useScenarioWorkspace() {
  const [snapshot, setSnapshot] = useState<WorkspaceSnapshot>(EMPTY_SNAPSHOT);

  useEffect(() => {
    setSnapshot(readSnapshot());
  }, []);

  const persist = useCallback((next: WorkspaceSnapshot) => {
    setSnapshot(next);
    writeSnapshot(next);
  }, []);

  const markRecent = useCallback(
    (slug: string) => {
      const cleanSlug = slug.trim();
      if (!cleanSlug) {
        return;
      }

      const next: WorkspaceSnapshot = {
        ...snapshot,
        recentSlugs: uniqueTrimmed([cleanSlug, ...snapshot.recentSlugs.filter((item) => item !== cleanSlug)], MAX_RECENT),
      };
      persist(next);
    },
    [persist, snapshot],
  );

  const toggleSaved = useCallback(
    (slug: string) => {
      const cleanSlug = slug.trim();
      if (!cleanSlug) {
        return;
      }

      const exists = snapshot.savedSlugs.includes(cleanSlug);
      const nextSaved = exists
        ? snapshot.savedSlugs.filter((item) => item !== cleanSlug)
        : uniqueTrimmed([cleanSlug, ...snapshot.savedSlugs], 64);

      persist({
        ...snapshot,
        savedSlugs: nextSaved,
      });
    },
    [persist, snapshot],
  );

  const saveUnfinished = useCallback(
    (slug: string, task: string) => {
      const cleanSlug = slug.trim();
      const cleanTask = task.trim();
      if (!cleanSlug || !cleanTask) {
        return;
      }

      const updatedAt = new Date().toISOString();
      const nextItem = { slug: cleanSlug, task: cleanTask, updatedAt };
      const nextUnfinished = [nextItem, ...snapshot.unfinished.filter((item) => item.slug !== cleanSlug)].slice(
        0,
        MAX_UNFINISHED,
      );

      persist({
        ...snapshot,
        unfinished: nextUnfinished,
      });
    },
    [persist, snapshot],
  );

  const clearUnfinished = useCallback(
    (slug: string) => {
      persist({
        ...snapshot,
        unfinished: snapshot.unfinished.filter((item) => item.slug !== slug),
      });
    },
    [persist, snapshot],
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
    }),
    [clearUnfinished, markRecent, saveUnfinished, snapshot.recentSlugs, snapshot.savedSlugs, snapshot.unfinished, toggleSaved],
  );
}
