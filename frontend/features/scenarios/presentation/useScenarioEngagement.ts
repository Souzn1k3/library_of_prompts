"use client";

import { useCallback, useMemo, useState } from "react";

import { trackPromptApply, trackPromptCopy } from "@/lib/client-api/prompts";

type EngagementState = {
  runPending: boolean;
  copyPending: boolean;
  latestBalanceDelta: number;
  latestMessage: string | null;
};

const INITIAL_STATE: EngagementState = {
  runPending: false,
  copyPending: false,
  latestBalanceDelta: 0,
  latestMessage: null,
};

function deriveBalanceDelta(payload: unknown): number {
  const candidate = payload as { balance_delta?: number } | null;
  if (!candidate || typeof candidate.balance_delta !== "number") {
    return 0;
  }
  return candidate.balance_delta;
}

export function useScenarioEngagement() {
  const [state, setState] = useState<EngagementState>(INITIAL_STATE);

  const markScenarioRun = useCallback(async (promptId: string) => {
    setState((current) => ({ ...current, runPending: true, latestMessage: null }));
    try {
      const result = await trackPromptApply(promptId);
      const delta = deriveBalanceDelta(result);
      setState((current) => ({
        ...current,
        runPending: false,
        latestBalanceDelta: delta,
        latestMessage: delta > 0 ? `+${delta} LMN` : "Run tracked",
      }));
      return { ok: true as const, delta };
    } catch {
      setState((current) => ({
        ...current,
        runPending: false,
        latestMessage: "Run tracked locally",
      }));
      return { ok: false as const, delta: 0 };
    }
  }, []);

  const markScenarioCopy = useCallback(async (promptId: string) => {
    setState((current) => ({ ...current, copyPending: true, latestMessage: null }));
    try {
      const result = await trackPromptCopy(promptId);
      const delta = deriveBalanceDelta(result);
      setState((current) => ({
        ...current,
        copyPending: false,
        latestBalanceDelta: delta,
        latestMessage: delta > 0 ? `+${delta} LMN` : "Copy tracked",
      }));
      return { ok: true as const, delta };
    } catch {
      setState((current) => ({
        ...current,
        copyPending: false,
        latestMessage: "Copy tracked locally",
      }));
      return { ok: false as const, delta: 0 };
    }
  }, []);

  const clearMessage = useCallback(() => {
    setState((current) => ({ ...current, latestMessage: null }));
  }, []);

  return useMemo(
    () => ({
      runPending: state.runPending,
      copyPending: state.copyPending,
      latestBalanceDelta: state.latestBalanceDelta,
      latestMessage: state.latestMessage,
      markScenarioRun,
      markScenarioCopy,
      clearMessage,
    }),
    [clearMessage, markScenarioCopy, markScenarioRun, state.copyPending, state.latestBalanceDelta, state.latestMessage, state.runPending],
  );
}
