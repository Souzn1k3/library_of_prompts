import { withQuery } from "@/lib/http";
import { API_ENDPOINTS } from "@/lib/constants/api";
import type { RevenueDashboard } from "@/lib/types";

import { apiFetch } from "./transport";

export async function fetchRevenueDashboard(
  accessToken: string | null | undefined,
  {
    windowDays = 30,
  }: {
    windowDays?: number;
  } = {},
): Promise<RevenueDashboard> {
  return apiFetch<RevenueDashboard>(
    withQuery(API_ENDPOINTS.analyticsRevenueDashboard, {
      window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
    }),
    { accessToken: accessToken ?? null },
  );
}

