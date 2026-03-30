"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ApiRequestError } from "@/lib/api";
import { clearLegacyAccessToken, subscribeAuthStateChange } from "@/lib/auth";
import { fetchMe, logoutRequest } from "@/lib/client-api";
import type { UserProfile } from "@/lib/types";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  isAuthenticated: boolean;
  user: UserProfile | null;
  refreshAuth: (options?: { background?: boolean }) => Promise<UserProfile | null>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  initialHasAuthCookie = false,
}: {
  children: React.ReactNode;
  initialHasAuthCookie?: boolean;
}) {
  const [status, setStatus] = useState<AuthStatus>(() =>
    initialHasAuthCookie ? "loading" : "unauthenticated",
  );
  const [user, setUser] = useState<UserProfile | null>(null);
  const mountedRef = useRef(true);
  const refreshPromiseRef = useRef<Promise<UserProfile | null> | null>(null);

  const applyUnauthenticated = useCallback(() => {
    if (!mountedRef.current) {
      return;
    }
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const refreshAuth = useCallback(
    (options?: { background?: boolean }) => {
      if (refreshPromiseRef.current) {
        return refreshPromiseRef.current;
      }

      if (!options?.background) {
        setStatus((current) => (current === "authenticated" ? "authenticated" : "loading"));
      }

      refreshPromiseRef.current = (async () => {
        try {
          const me = await fetchMe();
          if (!mountedRef.current) {
            return me;
          }
          setUser(me);
          setStatus("authenticated");
          return me;
        } catch (error) {
          if (!mountedRef.current) {
            return null;
          }
          if (error instanceof ApiRequestError && error.status === 401) {
            applyUnauthenticated();
            return null;
          }
          setStatus((current) => {
            if (user) {
              return "authenticated";
            }
            return initialHasAuthCookie && current === "loading" ? "loading" : "unauthenticated";
          });
          return user;
        } finally {
          refreshPromiseRef.current = null;
        }
      })();

      return refreshPromiseRef.current;
    },
    [applyUnauthenticated, initialHasAuthCookie, user],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      applyUnauthenticated();
    }
  }, [applyUnauthenticated]);

  useEffect(() => {
    mountedRef.current = true;
    clearLegacyAccessToken();
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!initialHasAuthCookie) {
      return;
    }
    void refreshAuth();
  }, [initialHasAuthCookie, refreshAuth]);

  useEffect(() => {
    return subscribeAuthStateChange(() => applyUnauthenticated());
  }, [applyUnauthenticated]);

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

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      isAuthenticated: status === "authenticated",
      user,
      refreshAuth,
      logout,
    }),
    [logout, refreshAuth, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
