import { getApiBaseUrl } from "@/lib/api";
import { isBrowser } from "@/lib/analytics/environment";
import type { AnalyticsPayloadEvent } from "@/lib/analytics/types";
import { API_ENDPOINTS } from "@/lib/constants/api";

const MAX_QUEUE_SIZE = 1000;
const FLUSH_BATCH_SIZE = 100;
const FLUSH_IMMEDIATE_THRESHOLD = 30;
const DEFAULT_FLUSH_DELAY_MS = 500;
const RETRY_FLUSH_DELAY_MS = 2000;

let queue: AnalyticsPayloadEvent[] = [];
let flushTimer: number | null = null;

function scheduleFlush(delayMs = DEFAULT_FLUSH_DELAY_MS) {
  if (!isBrowser()) return;
  if (flushTimer != null) return;
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    void flushAnalyticsQueue();
  }, delayMs);
}

async function flushAnalyticsQueue() {
  if (!isBrowser()) return;
  if (!queue.length) return;
  const batch = queue.slice(0, FLUSH_BATCH_SIZE);
  queue = queue.slice(FLUSH_BATCH_SIZE);

  try {
    const res = await fetch(`${getApiBaseUrl()}${API_ENDPOINTS.analyticsEvents}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ events: batch }),
      credentials: "include",
      keepalive: true,
      cache: "no-store",
    });

    if (!res.ok) {
      if (process.env.NODE_ENV !== "production") {
        console.warn("[analytics] ingest non-2xx", res.status);
      }
      if (res.status >= 500 || res.status === 429) {
        queue = [...batch, ...queue].slice(-MAX_QUEUE_SIZE);
        scheduleFlush(RETRY_FLUSH_DELAY_MS);
      }
    }
  } catch (err) {
    queue = [...batch, ...queue].slice(-MAX_QUEUE_SIZE);
    scheduleFlush(RETRY_FLUSH_DELAY_MS);
    if (process.env.NODE_ENV !== "production") {
      console.warn("[analytics] ingest failed", err);
    }
  } finally {
    if (queue.length) {
      scheduleFlush();
    }
  }
}

export function enqueueAnalyticsEvent(event: AnalyticsPayloadEvent) {
  queue.push(event);
  if (queue.length > MAX_QUEUE_SIZE) {
    queue = queue.slice(-MAX_QUEUE_SIZE);
  }
  if (queue.length >= FLUSH_IMMEDIATE_THRESHOLD) {
    void flushAnalyticsQueue();
    return;
  }
  scheduleFlush();
}
