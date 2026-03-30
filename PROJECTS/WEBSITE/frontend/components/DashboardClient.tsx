"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { DashboardView } from "@/components/dashboard/DashboardView";
import { useDashboardData } from "@/components/dashboard/useDashboardData";

export function DashboardClient() {
  const { status } = useAuth();
  const { reload, ...dashboard } = useDashboardData(status);

  return <DashboardView status={status} onReload={reload} {...dashboard} />;
}
