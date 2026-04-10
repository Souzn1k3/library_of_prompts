"use client";

import { useEffect, type MutableRefObject } from "react";

import { clearLegacyAccessToken, hasAuthSessionHint, subscribeAuthStateChange } from "@/lib/auth";
import type { UserProfile } from "@/lib/types";

const AUTH_STATE_COOKIE =
  process.env.NEXT_PUBLIC_AUTH_STATE_COOKIE_NAME ?? "pv_auth_state";
const ACCESS_TOKEN_COOKIE =
  process.env.NEXT_PUBLIC_ACCESS_TOKEN_COOKIE_NAME ?? "pv_access_token";
const REFRESH_TOKEN_COOKIE =
  process.env.NEXT_PUBLIC_REFRESH_TOKEN_COOKIE_NAME ?? "pv_refresh_token";

type RefreshAuthFn = (
  options?: { background?: boolean },
) => Promise<UserProfile | null>;

export function hasAuthCookieInBrowser() {
  if (typeof document === "undefined") {
    return false;
  }
  const pairs = document.cookie.split(";").map((item) => item.trim());
  const hasCookieSignal = pairs.some((pair) => {
    const [name] = pair.split("=");
    return (
      name === AUTH_STATE_COOKIE ||
      name === ACCESS_TOKEN_COOKIE ||
      name === REFRESH_TOKEN_COOKIE
    );
  });
  return hasCookieSignal || hasAuthSessionHint();
}

export function useAuthMountLifecycle(mountedRef: MutableRefObject<boolean>) {
  useEffect(() => {
    mountedRef.current = true;
    clearLegacyAccessToken();
    return () => {
      mountedRef.current = false;
    };
  }, [mountedRef]);
}

export function useAuthBootstrapSync({
  initialHasAuthCookie,
  refreshAuth,
  serverBootstrapDoneRef,
  clientBootstrapDoneRef,
  setStatusLoading,
}: {
  initialHasAuthCookie: boolean;
  refreshAuth: RefreshAuthFn;
  serverBootstrapDoneRef: MutableRefObject<boolean>;
  clientBootstrapDoneRef: MutableRefObject<boolean>;
  setStatusLoading: () => void;
}) {
  useEffect(() => {
    if (!initialHasAuthCookie) {
      return;
    }
    if (serverBootstrapDoneRef.current) {
      return;
    }
    serverBootstrapDoneRef.current = true;
    void refreshAuth();
  }, [initialHasAuthCookie, refreshAuth, serverBootstrapDoneRef]);

  useEffect(() => {
    if (initialHasAuthCookie) {
      return;
    }
    if (clientBootstrapDoneRef.current) {
      return;
    }
    if (!hasAuthCookieInBrowser()) {
      return;
    }
    clientBootstrapDoneRef.current = true;
    setStatusLoading();
    void refreshAuth();
  }, [
    initialHasAuthCookie,
    refreshAuth,
    clientBootstrapDoneRef,
    setStatusLoading,
  ]);
}

export function useAuthStateChangeSync(onUnauthenticated: () => void) {
  useEffect(() => {
    return subscribeAuthStateChange(() => onUnauthenticated());
  }, [onUnauthenticated]);
}

export function useAuthForegroundRevalidate(refreshAuth: RefreshAuthFn) {
  useEffect(() => {
    const revalidate = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") {
        return;
      }
      void refreshAuth({ background: true });
    };

    window.addEventListener("focus", revalidate);
    document.addEventListener("visibilitychange", revalidate);
    return () => {
      window.removeEventListener("focus", revalidate);
      document.removeEventListener("visibilitychange", revalidate);
    };
  }, [refreshAuth]);
}
