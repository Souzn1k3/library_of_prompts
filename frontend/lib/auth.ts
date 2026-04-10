const LEGACY_ACCESS_TOKEN_STORAGE_KEY = "pv_access_token";
const AUTH_SESSION_HINT_STORAGE_KEY = "pv_auth_session_hint";
const AUTH_STATE_EVENT = "pv-auth-state-change";

export type AuthStateChangeDetail = {
  reason: "logout" | "refresh" | "expired";
};

export function clearLegacyAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(LEGACY_ACCESS_TOKEN_STORAGE_KEY);
}

export function markAuthSessionHint(): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(AUTH_SESSION_HINT_STORAGE_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function clearAuthSessionHint(): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.removeItem(AUTH_SESSION_HINT_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function hasAuthSessionHint(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  try {
    return window.localStorage.getItem(AUTH_SESSION_HINT_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function emitAuthStateChange(detail: AuthStateChangeDetail): void {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new CustomEvent<AuthStateChangeDetail>(AUTH_STATE_EVENT, { detail }));
}

export function subscribeAuthStateChange(
  listener: (detail: AuthStateChangeDetail) => void,
): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const handler = (event: Event) => {
    const authEvent = event as CustomEvent<AuthStateChangeDetail>;
    if (!authEvent.detail) {
      return;
    }
    listener(authEvent.detail);
  };

  window.addEventListener(AUTH_STATE_EVENT, handler as EventListener);
  return () => window.removeEventListener(AUTH_STATE_EVENT, handler as EventListener);
}
