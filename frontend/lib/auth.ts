const LEGACY_ACCESS_TOKEN_STORAGE_KEY = "pv_access_token";
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
