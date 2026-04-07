import { API_ENDPOINTS } from "../constants/api";
import type {
  ScenarioDemoRunStatusRead,
  ScenarioDemoRunTrackRead,
  ScenarioDemoRunTrackRequest,
  ScenarioGameClaimRead,
  ScenarioGameClaimRequest,
  ScenarioGameEarnRead,
  ScenarioGameEarnRequest,
  ScenarioGameStateRead,
  ScenarioHomeAggregateRead,
  ScenarioRunEventRead,
  ScenarioWorkspaceRead,
  ScenarioWorkspaceTrackRequest,
} from "../types";
import { authFetch, jsonInit } from "./transport";

export async function fetchScenarioWorkspace(params?: {
  recent_limit?: number;
  saved_limit?: number;
  unfinished_limit?: number;
}): Promise<ScenarioWorkspaceRead> {
  const query = new URLSearchParams();
  if (params?.recent_limit) {
    query.set("recent_limit", String(params.recent_limit));
  }
  if (params?.saved_limit) {
    query.set("saved_limit", String(params.saved_limit));
  }
  if (params?.unfinished_limit) {
    query.set("unfinished_limit", String(params.unfinished_limit));
  }
  const suffix = query.toString();
  const path = suffix ? `${API_ENDPOINTS.scenariosWorkspace}?${suffix}` : API_ENDPOINTS.scenariosWorkspace;
  return authFetch<ScenarioWorkspaceRead>(path);
}

export async function trackScenarioWorkspaceAction(body: ScenarioWorkspaceTrackRequest): Promise<ScenarioRunEventRead> {
  return authFetch<ScenarioRunEventRead>(
    API_ENDPOINTS.scenariosWorkspaceTrack,
    jsonInit("POST", body),
  );
}

export async function fetchScenarioHomeAggregateClient(limit = 8): Promise<ScenarioHomeAggregateRead> {
  const path = `${API_ENDPOINTS.scenariosAggregate}?limit=${encodeURIComponent(String(limit))}`;
  return authFetch<ScenarioHomeAggregateRead>(path);
}

export async function fetchScenarioDemoRunStatus(promptSlug: string): Promise<ScenarioDemoRunStatusRead> {
  const path = `${API_ENDPOINTS.scenariosDemoRunStatus}?prompt_slug=${encodeURIComponent(promptSlug)}`;
  return authFetch<ScenarioDemoRunStatusRead>(path);
}

export async function trackScenarioDemoRun(body: ScenarioDemoRunTrackRequest): Promise<ScenarioDemoRunTrackRead> {
  return authFetch<ScenarioDemoRunTrackRead>(API_ENDPOINTS.scenariosDemoRunTrack, jsonInit("POST", body));
}

export async function fetchScenarioGameState(): Promise<ScenarioGameStateRead> {
  return authFetch<ScenarioGameStateRead>(API_ENDPOINTS.scenariosGameState);
}

export async function earnScenarioGameTokens(body: ScenarioGameEarnRequest): Promise<ScenarioGameEarnRead> {
  return authFetch<ScenarioGameEarnRead>(API_ENDPOINTS.scenariosGameEarn, jsonInit("POST", body));
}

export async function claimScenarioGameTokens(body?: ScenarioGameClaimRequest): Promise<ScenarioGameClaimRead> {
  return authFetch<ScenarioGameClaimRead>(API_ENDPOINTS.scenariosGameClaim, jsonInit("POST", body ?? {}));
}
