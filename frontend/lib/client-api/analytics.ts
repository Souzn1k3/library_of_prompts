import type { Attribution } from "@/lib/analytics/types";
import type {
  ChannelSpendUpsertRead,
  ChannelSpendUpsertWrite,
  GtmDashboard,
  RevenueDashboard,
} from "@/lib/types";
import { withQuery } from "@/lib/http";

import { API_ENDPOINTS } from "@/lib/constants/api";

import { authFetch, jsonInit, optionalAuthJsonFetch } from "./transport";

export type AttributionCaptureResponse = {
  session_id: string;
  user_id: string | null;
  first_touch: {
    utm_source: string | null;
    utm_medium: string | null;
    utm_campaign: string | null;
    ad_id: string | null;
    creative_id: string | null;
    referrer: string | null;
    seen_at: string;
  };
  last_touch: {
    utm_source: string | null;
    utm_medium: string | null;
    utm_campaign: string | null;
    ad_id: string | null;
    creative_id: string | null;
    referrer: string | null;
    seen_at: string;
  };
};

export async function captureAttribution({
  sessionId,
  attribution,
  source = "web",
  page = "/",
  feature = "attribution_capture",
}: {
  sessionId: string;
  attribution: Attribution;
  source?: string;
  page?: string;
  feature?: string;
}): Promise<AttributionCaptureResponse> {
  return optionalAuthJsonFetch<AttributionCaptureResponse>(API_ENDPOINTS.analyticsAttribution, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      attribution,
      source,
      page,
      feature,
    }),
  });
}

export async function fetchRevenueDashboard({
  windowDays = 30,
}: {
  windowDays?: number;
} = {}): Promise<RevenueDashboard> {
  const path = withQuery(API_ENDPOINTS.analyticsRevenueDashboard, {
    window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
  });
  return authFetch<RevenueDashboard>(path);
}

export async function fetchGtmDashboard({
  windowDays = 30,
}: {
  windowDays?: number;
} = {}): Promise<GtmDashboard> {
  const path = withQuery(API_ENDPOINTS.analyticsGtmDashboard, {
    window_days: Math.max(7, Math.min(90, Math.trunc(windowDays))),
  });
  return authFetch<GtmDashboard>(path);
}

export async function upsertGtmChannelSpend(
  payload: ChannelSpendUpsertWrite,
): Promise<ChannelSpendUpsertRead> {
  return authFetch<ChannelSpendUpsertRead>(
    API_ENDPOINTS.analyticsGtmSpend,
    jsonInit("POST", payload),
  );
}
