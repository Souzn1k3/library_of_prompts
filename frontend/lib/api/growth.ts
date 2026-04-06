import { withQuery } from "@/lib/http";
import { API_ENDPOINTS } from "@/lib/constants/api";
import type { GrowthDashboard } from "@/lib/types";

import { apiFetch } from "./transport";

export async function fetchGrowthDashboard(
  accessToken: string | null | undefined,
  {
    windowDays = 28,
  }: {
    windowDays?: number;
  } = {},
): Promise<GrowthDashboard> {
  return apiFetch<GrowthDashboard>(
    withQuery(API_ENDPOINTS.analyticsGrowthDashboard, {
      window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
    }),
    { accessToken: accessToken ?? null },
  );
}

