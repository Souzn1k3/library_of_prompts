import { isBrowser, randomId } from "@/lib/analytics/environment";
import type { Attribution } from "@/lib/analytics/types";

const SESSION_STORAGE_KEY = "pv_analytics_session_id";
const ATTR_STORAGE_KEY = "pv_analytics_attribution_v1";
const ONCE_KEYS_STORAGE_KEY = "pv_analytics_once_keys_v1";
const MAX_ONCE_KEYS = 1000;

const onceKeys = new Set<string>();
let onceKeysLoaded = false;

export function analyticsSessionId(): string {
  if (!isBrowser()) return "server";
  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) return existing;
  const next = `sess_${randomId()}`;
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, next);
  return next;
}

export function readAttribution(): Attribution {
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

export function registerOnceKey(onceKey?: string): boolean {
  if (!onceKey) {
    return true;
  }
  loadOnceKeys();
  if (onceKeys.has(onceKey)) {
    return false;
  }
  onceKeys.add(onceKey);
  while (onceKeys.size > MAX_ONCE_KEYS) {
    const first = onceKeys.values().next().value;
    if (!first) break;
    onceKeys.delete(first);
  }
  persistOnceKeys();
  return true;
}
