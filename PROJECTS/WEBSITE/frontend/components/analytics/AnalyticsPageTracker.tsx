"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { analyticsSessionId, trackEvent } from "@/lib/analytics";

export function AnalyticsPageTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const query = searchParams.toString();
    const page = query ? `${pathname}?${query}` : pathname;
    const sessionId = analyticsSessionId();

    trackEvent({
      eventName: "first_visit",
      page,
      feature: "session",
      onceKey: `first_visit:${sessionId}`,
      metadata: {
        pathname,
      },
    });

    trackEvent({
      eventName: "page_viewed",
      page,
      feature: "navigation",
      onceKey: `page_viewed:${page}`,
      metadata: {
        pathname,
        query,
      },
    });
  }, [pathname, searchParams]);

  return null;
}

