import type { GtmDashboard } from "@/lib/types";

import { withQuery } from "@/lib/http";
import { API_ENDPOINTS } from "@/lib/constants/api";

import { apiFetch } from "./transport";

export async function fetchGtmDashboard(
  accessToken: string | null | undefined,
  {
    windowDays = 30,
  }: {
    windowDays?: number;
  } = {},
): Promise<GtmDashboard> {
  const path = withQuery(API_ENDPOINTS.analyticsGtmDashboard, {
    window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
  });
  return apiFetch<GtmDashboard>(path, {
    accessToken,
    cache: "no-store",
  });
}

