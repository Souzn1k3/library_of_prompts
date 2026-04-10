"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  useAuthBootstrapSync,
  useAuthForegroundRevalidate,
  useAuthMountLifecycle,
  useAuthStateChangeSync,
} from "@/components/auth/authProviderEffects";
import { clearAuthSessionHint, markAuthSessionHint } from "@/lib/auth";
import { ApiRequestError } from "@/lib/api";
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
  const serverBootstrapDoneRef = useRef(false);
  const clientBootstrapDoneRef = useRef(false);

  const applyUnauthenticated = useCallback(() => {
    if (!mountedRef.current) {
      return;
    }
    clearAuthSessionHint();
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
          markAuthSessionHint();
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

  useAuthMountLifecycle(mountedRef);
  useAuthBootstrapSync({
    initialHasAuthCookie,
    refreshAuth,
    serverBootstrapDoneRef,
    clientBootstrapDoneRef,
    setStatusLoading: () => setStatus((current) => (current === "authenticated" ? current : "loading")),
  });
  useAuthStateChangeSync(applyUnauthenticated);
  useAuthForegroundRevalidate(refreshAuth);

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
