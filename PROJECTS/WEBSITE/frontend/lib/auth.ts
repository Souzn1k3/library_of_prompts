const STORAGE_KEY = "pv_access_token";
const AUTH_STATE_EVENT = "pv-auth-state-change";

export type AuthStateChangeDetail = {
  state: "authenticated" | "unauthenticated";
  reason: "login" | "logout" | "refresh" | "expired";
};

export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") {
    return;
  }
  // Do not persist new access tokens in JS-accessible storage.
  // Keep only legacy-token cleanup to support a safe migration path.
  if (!token) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
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
