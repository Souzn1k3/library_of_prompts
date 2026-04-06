"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchScenarioDemoRunStatus, purchaseScenarioDemoRunBoost, trackScenarioDemoRun } from "@/lib/client-api";
import type { ScenarioDemoRunStatusRead } from "@/lib/types";

type UseScenarioDemoRunState = {
  status: ScenarioDemoRunStatusRead | null;
  loading: boolean;
  runPending: boolean;
  boostPending: boolean;
  latestMessage: string | null;
};

const INITIAL_STATE: UseScenarioDemoRunState = {
  status: null,
  loading: false,
  runPending: false,
  boostPending: false,
  latestMessage: null,
};

export function useScenarioDemoRun(promptSlug: string | null) {
  const [state, setState] = useState<UseScenarioDemoRunState>(INITIAL_STATE);

  const refresh = useCallback(async () => {
    if (!promptSlug) {
      setState(INITIAL_STATE);
      return null;
    }

    setState((current) => ({ ...current, loading: true }));
    try {
      const status = await fetchScenarioDemoRunStatus(promptSlug);
      setState((current) => ({
        ...current,
        status,
        loading: false,
      }));
      return status;
    } catch {
      setState((current) => ({ ...current, loading: false }));
      return null;
    }
  }, [promptSlug]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = useCallback(
    async (taskInput?: string | null) => {
      if (!promptSlug) {
        return null;
      }

      setState((current) => ({ ...current, runPending: true, latestMessage: null }));
      try {
        const result = await trackScenarioDemoRun({
          prompt_slug: promptSlug,
          task_input: taskInput ?? undefined,
        });
        setState((current) => ({
          ...current,
          runPending: false,
          status: result.status,
          latestMessage: result.executed
            ? result.status.cap_reached
              ? "free_demo_cap_reached"
              : null
            : result.status.reason ?? "run_limit_reached",
        }));
        return result;
      } catch {
        setState((current) => ({
          ...current,
          runPending: false,
          latestMessage: "run_unavailable",
        }));
        return null;
      }
    },
    [promptSlug],
  );

  const purchaseBoost = useCallback(async () => {
    if (!promptSlug) {
      return null;
    }
    setState((current) => ({ ...current, boostPending: true, latestMessage: null }));
    try {
      const purchase = await purchaseScenarioDemoRunBoost({ prompt_slug: promptSlug });
      const status = await fetchScenarioDemoRunStatus(promptSlug);
      setState((current) => ({
        ...current,
        boostPending: false,
        status,
        latestMessage: purchase.is_pro
          ? "pro_unlimited_runs"
          : `bonus_runs_added:${purchase.applied_bonus_runs}`,
      }));
      return purchase;
    } catch {
      setState((current) => ({
        ...current,
        boostPending: false,
        latestMessage: "boost_purchase_failed",
      }));
      return null;
    }
  }, [promptSlug]);

  return useMemo(
    () => ({
      status: state.status,
      loading: state.loading,
      runPending: state.runPending,
      boostPending: state.boostPending,
      latestMessage: state.latestMessage,
      refresh,
      run,
      purchaseBoost,
      canRun: Boolean(state.status?.allowed),
      remainingRuns: state.status?.remaining_runs ?? null,
      bonusRunsRemaining: state.status?.bonus_runs_remaining ?? null,
      capReached: Boolean(state.status?.cap_reached),
      isPro: Boolean(state.status?.is_pro),
    }),
    [purchaseBoost, refresh, run, state.boostPending, state.latestMessage, state.loading, state.runPending, state.status],
  );
}
