import { getApiBaseUrl } from "@/lib/api";
import { getToken } from "@/lib/auth";

export type AnalyticsEventName =
  | "signup_completed"
  | "first_visit"
  | "page_viewed"
  | "onboarding_started"
  | "onboarding_completed"
  | "onboarding_first_action"
  | "prompt_viewed"
  | "prompt_copied"
  | "prompt_saved"
  | "mission_started"
  | "mission_progressed"
  | "mission_completed"
  | "mission_next_step_clicked"
  | "submission_form_submitted"
  | "submission_created"
  | "submission_moderated"
  | "submission_engaged"
  | "locked_content_viewed"
  | "upgrade_clicked"
  | "checkout_started"
  | "subscription_activated"
  | "catalog_search_used"
  | "catalog_filter_used";

type AnalyticsPayloadEvent = {
  event_id: string;
  event_name: AnalyticsEventName;
  session_id: string;
  timestamp: string;
  source: "web";
  context: {
    page: string;
    feature: string;
  };
  attribution: {
    utm_source?: string;
    utm_medium?: string;
    utm_campaign?: string;
    utm_term?: string;
    utm_content?: string;
    referrer?: string;
  };
  metadata: Record<string, unknown>;
};

type TrackEventInput = {
  eventName: AnalyticsEventName;
  page: string;
  feature: string;
  metadata?: Record<string, unknown>;
  onceKey?: string;
};

type Attribution = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  referrer?: string;
};

const SESSION_STORAGE_KEY = "pv_analytics_session_id";
const ATTR_STORAGE_KEY = "pv_analytics_attribution_v1";
const ONCE_KEYS_STORAGE_KEY = "pv_analytics_once_keys_v1";
const MAX_QUEUE_SIZE = 1000;
const MAX_ONCE_KEYS = 1000;

let queue: AnalyticsPayloadEvent[] = [];
let flushTimer: number | null = null;
const onceKeys = new Set<string>();
let onceKeysLoaded = false;

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function randomId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

export function analyticsSessionId(): string {
  if (!isBrowser()) return "server";
  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) return existing;
  const next = `sess_${randomId()}`;
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, next);
  return next;
}

function readAttribution(): Attribution {
  if (!isBrowser()) return {};
  let storedAttr: Attribution = {};
  const stored = window.localStorage.getItem(ATTR_STORAGE_KEY);
  if (stored) {
    try {
      storedAttr = JSON.parse(stored) as Attribution;
    } catch {
      storedAttr = {};
    }
  }

  const params = new URLSearchParams(window.location.search);
  const nextAttr: Attribution = {
    ...storedAttr,
  };
  const replacements: Array<keyof Attribution> = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
  ];
  for (const key of replacements) {
    const value = params.get(key);
    if (value) {
      nextAttr[key] = value;
    }
  }
  if (!nextAttr.referrer && document.referrer) {
    nextAttr.referrer = document.referrer;
  }

  window.localStorage.setItem(ATTR_STORAGE_KEY, JSON.stringify(nextAttr));
  return nextAttr;
}

function loadOnceKeys() {
  if (!isBrowser() || onceKeysLoaded) return;
  onceKeysLoaded = true;
  const raw = window.sessionStorage.getItem(ONCE_KEYS_STORAGE_KEY);
  if (!raw) return;
  try {
    const values = JSON.parse(raw) as string[];
    for (const value of values.slice(-MAX_ONCE_KEYS)) {
      if (typeof value === "string" && value.length > 0) {
        onceKeys.add(value);
      }
    }
  } catch {
    // ignore malformed storage payload
  }
}

function persistOnceKeys() {
  if (!isBrowser()) return;
  const values = Array.from(onceKeys).slice(-MAX_ONCE_KEYS);
  window.sessionStorage.setItem(ONCE_KEYS_STORAGE_KEY, JSON.stringify(values));
}

function scheduleFlush(delayMs = 500) {
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
  const batch = queue.slice(0, 100);
  queue = queue.slice(100);

  try {
    const token = getToken();
    const res = await fetch(`${getApiBaseUrl()}/api/v1/analytics/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
        scheduleFlush(2000);
      }
    }
  } catch (err) {
    queue = [...batch, ...queue].slice(-MAX_QUEUE_SIZE);
    scheduleFlush(2000);
    if (process.env.NODE_ENV !== "production") {
      console.warn("[analytics] ingest failed", err);
    }
  } finally {
    if (queue.length) {
      scheduleFlush();
    }
  }
}

export function trackEvent(input: TrackEventInput) {
  if (!isBrowser()) return;
  loadOnceKeys();
  if (input.onceKey && onceKeys.has(input.onceKey)) return;
  if (input.onceKey) {
    onceKeys.add(input.onceKey);
    while (onceKeys.size > MAX_ONCE_KEYS) {
      const first = onceKeys.values().next().value;
      if (!first) break;
      onceKeys.delete(first);
    }
    persistOnceKeys();
  }

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

  queue.push(event);
  if (queue.length > MAX_QUEUE_SIZE) {
    queue = queue.slice(-MAX_QUEUE_SIZE);
  }
  if (queue.length >= 30) {
    void flushAnalyticsQueue();
    return;
  }
  scheduleFlush();
}
