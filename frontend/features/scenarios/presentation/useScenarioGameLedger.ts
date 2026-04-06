"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { claimScenarioGameTokens, earnScenarioGameTokens, fetchScenarioGameState } from "@/lib/client-api";
import type { ScenarioGameStateRead } from "@/lib/types";

type GameLedgerState = {
  gameState: ScenarioGameStateRead | null;
  loading: boolean;
  earnPending: boolean;
  claimPending: boolean;
  latestMessage: string | null;
};

const INITIAL_STATE: GameLedgerState = {
  gameState: null,
  loading: false,
  earnPending: false,
  claimPending: false,
  latestMessage: null,
};

function createEventId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `web-demo-${crypto.randomUUID()}`;
  }
  return `web-demo-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function useScenarioGameLedger() {
  const [state, setState] = useState<GameLedgerState>(INITIAL_STATE);

  const refresh = useCallback(async () => {
    setState((current) => ({ ...current, loading: true }));
    try {
      const gameState = await fetchScenarioGameState();
      setState((current) => ({ ...current, loading: false, gameState }));
      return gameState;
    } catch {
      setState((current) => ({ ...current, loading: false }));
      return null;
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const earn = useCallback(async (challengeId: string, choiceIndex: number) => {
    setState((current) => ({ ...current, earnPending: true, latestMessage: null }));
    try {
      const result = await earnScenarioGameTokens({
        event_id: createEventId(),
        challenge_id: challengeId,
        choice_index: choiceIndex,
      });
      const nextState = await fetchScenarioGameState().catch(() => null);
      setState((current) => ({
        ...current,
        earnPending: false,
        gameState: nextState ?? current.gameState,
        latestMessage:
          result.accepted && result.reward_tokens > 0
            ? `+${result.reward_tokens} pending tokens`
            : result.reason === "challenge_cooldown_active"
              ? "Challenge cooldown is active."
              : result.reason === "daily_cap_reached"
                ? "Daily demo reward cap reached."
                : result.reason === "guest_ip_daily_cap_reached"
                  ? "Network daily reward cap reached for guests."
                  : result.reason === "guest_fingerprint_daily_cap_reached"
                    ? "Device daily reward cap reached for guests."
                    : result.reason === "guest_rate_limited"
                      ? "Too many reward attempts. Try again later."
                : "Reward not granted.",
      }));
      return result;
    } catch {
      setState((current) => ({
        ...current,
        earnPending: false,
        latestMessage: "Reward event failed.",
      }));
      return null;
    }
  }, []);

  const claim = useCallback(async () => {
    setState((current) => ({ ...current, claimPending: true, latestMessage: null }));
    try {
      const claimId = createEventId();
      const result = await claimScenarioGameTokens({ claim_id: claimId });
      const nextState = await fetchScenarioGameState().catch(() => null);
      setState((current) => ({
        ...current,
        claimPending: false,
        gameState: nextState ?? current.gameState,
        latestMessage: result.applied
          ? `Claimed ${result.claimed_tokens} tokens`
          : "Nothing to claim yet.",
      }));
      return result;
    } catch {
      setState((current) => ({
        ...current,
        claimPending: false,
        latestMessage: "Claim requires an active account.",
      }));
      return null;
    }
  }, []);

  return useMemo(
    () => ({
      gameState: state.gameState,
      loading: state.loading,
      earnPending: state.earnPending,
      claimPending: state.claimPending,
      latestMessage: state.latestMessage,
      refresh,
      earn,
      claim,
    }),
    [claim, earn, refresh, state.claimPending, state.earnPending, state.gameState, state.latestMessage, state.loading],
  );
}
