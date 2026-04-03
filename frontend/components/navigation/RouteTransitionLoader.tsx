"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";

const ROUTE_TRANSITION_START_EVENT = "pv:route-transition-start";
const LOADER_SHOW_DELAY_MS = 90;
const LOADER_HIDE_DELAY_MS = 140;
const LOADER_FAILSAFE_MS = 10000;

function cleanupTimer(timerRef: MutableRefObject<number | null>) {
  if (timerRef.current !== null) {
    window.clearTimeout(timerRef.current);
    timerRef.current = null;
  }
}

export function startRouteTransitionLoader() {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(ROUTE_TRANSITION_START_EVENT));
}

export function RouteTransitionLoader() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isVisible, setIsVisible] = useState(false);
  const inFlightRef = useRef(false);
  const showTimerRef = useRef<number | null>(null);
  const hideTimerRef = useRef<number | null>(null);
  const failSafeTimerRef = useRef<number | null>(null);

  const routeKey = useMemo(() => {
    const query = searchParams.toString();
    return query ? `${pathname}?${query}` : pathname;
  }, [pathname, searchParams]);

  const start = useCallback(() => {
    if (inFlightRef.current) {
      return;
    }

    inFlightRef.current = true;
    cleanupTimer(hideTimerRef);
    cleanupTimer(showTimerRef);
    cleanupTimer(failSafeTimerRef);
    showTimerRef.current = window.setTimeout(() => {
      setIsVisible(true);
      showTimerRef.current = null;
    }, LOADER_SHOW_DELAY_MS);
    failSafeTimerRef.current = window.setTimeout(() => {
      inFlightRef.current = false;
      setIsVisible(false);
      failSafeTimerRef.current = null;
    }, LOADER_FAILSAFE_MS);
  }, []);

  const finish = useCallback(() => {
    if (!inFlightRef.current) {
      return;
    }

    inFlightRef.current = false;
    cleanupTimer(showTimerRef);
    cleanupTimer(hideTimerRef);
    cleanupTimer(failSafeTimerRef);
    hideTimerRef.current = window.setTimeout(() => {
      setIsVisible(false);
      hideTimerRef.current = null;
    }, LOADER_HIDE_DELAY_MS);
  }, []);

  useEffect(() => {
    finish();
  }, [finish, routeKey]);

  useEffect(() => {
    const onAnyNavigationStart = () => {
      start();
    };

    const onDocumentClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0) {
        return;
      }

      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }

      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }

      const link = target.closest("a");
      if (!(link instanceof HTMLAnchorElement)) {
        return;
      }

      if (link.target && link.target !== "_self") {
        return;
      }

      if (link.hasAttribute("download")) {
        return;
      }

      const href = link.getAttribute("href");
      if (!href || href.startsWith("#")) {
        return;
      }

      let currentUrl: URL;
      let nextUrl: URL;
      try {
        currentUrl = new URL(window.location.href);
        nextUrl = new URL(link.href, window.location.href);
      } catch {
        return;
      }

      if (nextUrl.origin !== currentUrl.origin) {
        return;
      }

      const isSameRoute = nextUrl.pathname === currentUrl.pathname && nextUrl.search === currentUrl.search;
      if (isSameRoute) {
        return;
      }

      start();
    };

    window.addEventListener(ROUTE_TRANSITION_START_EVENT, onAnyNavigationStart);
    document.addEventListener("click", onDocumentClick, true);

    return () => {
      window.removeEventListener(ROUTE_TRANSITION_START_EVENT, onAnyNavigationStart);
      document.removeEventListener("click", onDocumentClick, true);
      cleanupTimer(showTimerRef);
      cleanupTimer(hideTimerRef);
      cleanupTimer(failSafeTimerRef);
    };
  }, [start]);

  return (
    <div
      className={`pv-route-loader ${isVisible ? "pv-route-loader-visible" : ""}`}
      role="status"
      aria-live="polite"
      aria-label="Loading page"
      aria-hidden={!isVisible}
    >
      <div className="pv-route-loader-track">
        <div className="pv-route-loader-bar" />
      </div>
    </div>
  );
}
