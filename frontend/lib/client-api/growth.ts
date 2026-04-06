import type { GrowthDashboard, GrowthRuntime } from "@/lib/types";

import { withQuery } from "@/lib/http";
import { API_ENDPOINTS } from "@/lib/constants/api";

import { authFetch, optionalAuthJsonFetch } from "./transport";

export async function fetchGrowthRuntime({
  sessionId,
  page,
  feature,
}: {
  sessionId: string;
  page: string;
  feature: string;
}): Promise<GrowthRuntime> {
  const path = withQuery(API_ENDPOINTS.analyticsGrowthRuntime, {
    session_id: sessionId,
    page,
    feature,
  });
  return optionalAuthJsonFetch<GrowthRuntime>(path);
}

export async function fetchGrowthDashboard({
  windowDays = 28,
}: {
  windowDays?: number;
} = {}): Promise<GrowthDashboard> {
  const path = withQuery(API_ENDPOINTS.analyticsGrowthDashboard, {
    window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
  });
  return authFetch<GrowthDashboard>(path);
}

