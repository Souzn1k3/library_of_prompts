import { API_ENDPOINTS } from "../constants/api";
import { withQuery } from "../http";
import type { ScenarioHomeAggregateRead } from "../types";
import type { Language } from "../i18n";
import { apiFetch } from "./transport";

export async function fetchScenarioHomeAggregate(params?: {
  limit?: number;
  accessToken?: string | null;
  language?: Language | string | null;
}): Promise<ScenarioHomeAggregateRead> {
  return apiFetch<ScenarioHomeAggregateRead>(withQuery(API_ENDPOINTS.scenariosAggregate, { limit: params?.limit }), {
    accessToken: params?.accessToken,
    language: params?.language,
  });
}
