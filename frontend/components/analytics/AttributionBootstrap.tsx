"use client";

import { useEffect } from "react";

import { analyticsSessionId, trackEvent } from "@/lib/analytics";
import { readAttribution } from "@/lib/analytics/storage";
import { captureAttribution } from "@/lib/client-api";

const ATTR_SENT_KEY = "pv_attr_sent_v1";

export function AttributionBootstrap() {
  useEffect(() => {
    const sessionId = analyticsSessionId();
    const attribution = readAttribution();
    const storageKey = `${ATTR_SENT_KEY}:${sessionId}:${window.location.pathname}:${window.location.search}`;

    if (window.sessionStorage.getItem(storageKey) === "1") {
      return;
    }
    window.sessionStorage.setItem(storageKey, "1");

    void captureAttribution({
      sessionId,
      attribution,
    })
      .then((payload) => {
        trackEvent({
          eventName: "attribution_assigned",
          page: window.location.pathname,
          feature: "attribution_bootstrap",
          onceKey: `attribution_assigned:${payload.session_id}:${payload.last_touch.seen_at}`,
          metadata: {
            session_id: payload.session_id,
            user_id: payload.user_id,
            first_touch_source: payload.first_touch.utm_source,
            last_touch_source: payload.last_touch.utm_source,
          },
        });
      })
      .catch(() => null);
  }, []);

  return null;
}

