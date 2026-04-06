import { API_ENDPOINTS } from "../constants/api";
import type {
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
