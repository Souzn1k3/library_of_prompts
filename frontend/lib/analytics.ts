import { isBrowser, randomId } from "@/lib/analytics/environment";
import { enqueueAnalyticsEvent } from "@/lib/analytics/queue";
import { analyticsSessionId, readAttribution, registerOnceKey } from "@/lib/analytics/storage";
import type { AnalyticsPayloadEvent, TrackEventInput } from "@/lib/analytics/types";

export type { AnalyticsEventName } from "@/lib/analytics/types";

export { analyticsSessionId };

export function trackEvent(input: TrackEventInput) {
  if (!isBrowser()) return;
  if (!registerOnceKey(input.onceKey)) return;

  const event: AnalyticsPayloadEvent = {
    event_id: `evt_${randomId()}`,
    event_name: input.eventName,
    session_id: analyticsSessionId(),
    timestamp: new Date().toISOString(),
    source: "web",
    context: {
      page: input.page,
      feature: input.feature,
    },
    attribution: readAttribution(),
    metadata: input.metadata ?? {},
  };

  enqueueAnalyticsEvent(event);
}
