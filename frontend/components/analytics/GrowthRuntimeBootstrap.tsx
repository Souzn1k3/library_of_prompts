"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { analyticsSessionId } from "@/lib/analytics";
import { fetchGrowthRuntime } from "@/lib/client-api";

export function GrowthRuntimeBootstrap() {
  const pathname = usePathname();

  useEffect(() => {
    const sessionId = analyticsSessionId();
    const page = pathname || "/";

    void fetchGrowthRuntime({
      sessionId,
      page,
      feature: "runtime_bootstrap",
    }).catch(() => null);
  }, [pathname]);

  return null;
}

